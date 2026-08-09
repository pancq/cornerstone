"""告警服务"""
import asyncio
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from datetime import datetime
import httpx
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
import json
import logging

from src.models.alert import AlertRule, AlertRecord, AlertNotification
from src.models.device import Device
from src.models.link_monitor import LinkMonitor
from src.models.setting import Setting
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger()

NOTIFICATION_SETTINGS_KEY = "notification_settings"


class AlertService:
    """告警服务"""
    
    @staticmethod
    async def evaluate_rules(db: AsyncSession, device_id: int, target_ip: str, 
                            latency: float, packet_loss: float, status: str) -> List[dict]:
        """
        评估告警规则，生成告警记录
        
        返回：触发的告警列表
        """
        alerts = []
        
        # 获取适用的告警规则
        query = select(AlertRule).where(
            AlertRule.enabled == True,
            (AlertRule.device_id == device_id) | (AlertRule.device_id == None)
        )
        result = await db.execute(query)
        rules = result.scalars().all()
        logger.info(f"[evaluate_rules] device_id={device_id} target_ip={target_ip} "
                    f"latency={latency} packet_loss={packet_loss} status={status} "
                    f"found {len(rules)} enabled rules")
        
        for rule in rules:
            if await AlertService._check_condition(rule, latency, packet_loss, status):
                logger.info(f"[evaluate_rules] device_id={device_id} rule={rule.id} name={rule.name} "
                            f"condition_type={rule.condition_type} severity={rule.severity} condition matched")
                # 检查是否已有相同类型的活动告警
                existing_query = select(AlertRecord).where(
                    AlertRecord.device_id == device_id,
                    AlertRecord.rule_id == rule.id,
                    AlertRecord.status == "active"
                )
                existing_result = await db.execute(existing_query)
                existing_alert = existing_result.scalar_one_or_none()
                
                if not existing_alert:
                    logger.info(f"[evaluate_rules] device_id={device_id} rule={rule.id} no existing active alert, creating new")
                    # 创建新告警
                    alert_record = AlertRecord(
                        rule_id=rule.id,
                        device_id=device_id,
                        target_ip=target_ip,
                        alert_type=rule.condition_type,
                        severity=rule.severity,
                        message=AlertService._generate_message(rule, latency, packet_loss, status),
                        current_value=AlertService._get_current_value(rule, latency, packet_loss, status),
                        threshold=rule.threshold
                    )
                    db.add(alert_record)
                    await db.flush()
                    
                    # 发送通知
                    await AlertService._send_notifications(db, alert_record)

                    # critical 告警触发 AI 根因分析
                    if rule.severity == "critical":
                        logger.info(f"[evaluate_rules] device_id={device_id} rule={rule.id} new critical alert, triggering AI analysis")
                        await AlertService._perform_ai_analysis(db, alert_record)

                    logger.info(f"[evaluate_rules] device_id={device_id} rule={rule.id} new alert created, id={alert_record.id}")
                    alerts.append({
                        "id": alert_record.id,
                        "rule_id": rule.id,
                        "device_id": device_id,
                        "severity": rule.severity,
                        "message": alert_record.message
                    })
                else:
                    # 更新现有告警信息
                    logger.info(f"[evaluate_rules] device_id={device_id} rule={rule.id} existing active alert exists, updating")
                    old_severity = existing_alert.severity
                    existing_alert.message = AlertService._generate_message(rule, latency, packet_loss, status)
                    existing_alert.current_value = AlertService._get_current_value(rule, latency, packet_loss, status)
                    await db.flush()
                    
                    # 检查是否需要重新发送通知
                    severity_order = {"info": 0, "warning": 1, "critical": 2}
                    old_level = severity_order.get(old_severity, 0)
                    new_level = severity_order.get(rule.severity, 0)
                    
                    should_send = False
                    reason = ""
                    
                    if new_level > old_level:
                        # 严重度升级，需要重新发送通知
                        should_send = True
                        reason = f"告警严重度升级: {old_severity} -> {rule.severity}"
                        logger.info(f"[evaluate_rules] device_id={device_id} rule={rule.id} {reason}, will resend notification")
                    else:
                        # 检查上次通知时间
                        last_notification_query = select(AlertNotification).where(
                            AlertNotification.record_id == existing_alert.id,
                            AlertNotification.status == "sent"
                        ).order_by(AlertNotification.sent_at.desc()).limit(1)
                        last_notification_result = await db.execute(last_notification_query)
                        last_notification = last_notification_result.scalar_one_or_none()
                        
                        if not last_notification:
                            # 从未发送过通知
                            should_send = True
                            reason = "告警从未发送过通知"
                        elif last_notification.sent_at:
                            hours_since_last = (datetime.now() - last_notification.sent_at).total_seconds() / 3600
                            if hours_since_last >= 24:
                                # 超过24小时，重新发送
                                should_send = True
                                reason = f"告警已超过24小时（{hours_since_last:.1f}h），重新发送"
                    
                    if should_send:
                        logger.info(f"设备 [{device_id}] 告警重新发送通知: {reason}")
                        await AlertService._send_notifications(db, existing_alert)

                        # 升级到 critical 时触发 AI 根因分析
                        if new_level > old_level and rule.severity == "critical":
                            await AlertService._perform_ai_analysis(db, existing_alert)
                    
                    alerts.append({
                        "id": existing_alert.id,
                        "rule_id": rule.id,
                        "device_id": device_id,
                        "severity": rule.severity,
                        "message": existing_alert.message
                    })
        
        return alerts
    
    @staticmethod
    async def _check_condition(rule: AlertRule, latency: float, packet_loss: float, status: str) -> bool:
        """检查告警条件是否满足"""
        value = None
        
        if rule.condition_type == "latency" and latency is not None:
            value = latency
        elif rule.condition_type == "packet_loss" and packet_loss is not None:
            value = packet_loss
        elif rule.condition_type == "status":
            return status != "normal"
        
        if value is None:
            return False
        
        # 比较操作
        if rule.operator == "gt":
            return value > rule.threshold
        elif rule.operator == "lt":
            return value < rule.threshold
        elif rule.operator == "eq":
            return value == rule.threshold
        elif rule.operator == "ne":
            return value != rule.threshold
        
        return False
    
    @staticmethod
    def _generate_message(rule: AlertRule, latency: float, packet_loss: float, status: str) -> str:
        """生成告警消息"""
        status_text: dict[str, str] = {
            "critical": "严重",
            "warning": "警告",
            "info": "提示",
            "normal": "正常",
        }
        status_cn = status_text.get(status, status)

        if rule.condition_type == "latency":
            return f"设备延迟过高: 当前 {latency}ms, 阈值 {rule.threshold}ms"
        elif rule.condition_type == "packet_loss":
            return f"设备丢包率过高: 当前 {packet_loss}%, 阈值 {rule.threshold}%"
        elif rule.condition_type == "status":
            return f"设备状态异常: {statusCn}"
        return f"告警触发: {rule.name}"
    
    @staticmethod
    def _get_current_value(rule: AlertRule, latency: float, packet_loss: float, status: str) -> Optional[float]:
        """获取当前值"""
        if rule.condition_type == "latency":
            return latency
        elif rule.condition_type == "packet_loss":
            return packet_loss
        return None
    
    @staticmethod
    async def _perform_ai_analysis(db: AsyncSession, alert_record: AlertRecord):
        """对 critical 告警执行 AI 根因分析，结果存入 ai_analysis 字段"""
        try:
            from src.services.ai_client import get_ai_config, call_ai

            ai_config = await get_ai_config(db)
            if not ai_config:
                logger.debug("[AI根因分析] 无AI配置，跳过根因分析")
                return

            # 获取设备信息
            device = await db.get(Device, alert_record.device_id)
            device_name = device.name if device else "未知设备"
            device_type = device.type if device else "未知"
            device_brand = getattr(device, "brand", "") or ""
            device_model = getattr(device, "model", "") or ""

            logger.info(f"[AI根因分析] alert_id={alert_record.id} device={device_name} "
                        f"provider={ai_config.provider} model={ai_config.model} 开始调用AI")

            prompt = (
                f"请对以下 IT 基础设施告警进行根因分析，给出可能的故障原因和处理建议。\n\n"
                f"告警信息：\n"
                f"- 设备名称：{device_name}\n"
                f"- 设备类型：{device_type}\n"
                f"- 品牌/型号：{device_brand} {device_model}\n"
                f"- 目标IP：{alert_record.target_ip or 'N/A'}\n"
                f"- 告警类型：{alert_record.alert_type}\n"
                f"- 严重级别：{alert_record.severity}\n"
                f"- 告警消息：{alert_record.message}\n"
                f"- 当前值：{alert_record.current_value}\n"
                f"- 阈值：{alert_record.threshold}\n\n"
                f"请按以下格式输出：\n"
                f"1. 可能根因（列出 2-3 个最可能的原因，按可能性排序）\n"
                f"2. 排查步骤（每个根因对应的排查方法）\n"
                f"3. 处理建议（优先级排序的修复方案）"
            )

            system = (
                "你是一位资深的 IT 基础设施运维专家，擅长网络设备、服务器、存储等基础设施的故障诊断。"
                "请基于告警信息进行专业、准确的根因分析，输出简洁实用的分析报告。"
            )

            result = await call_ai(prompt, system, ai_config, max_tokens=1500, timeout=20)
            result_len = len(result) if result else 0
            alert_record.ai_analysis = result
            await db.flush()
            logger.info(f"[AI根因分析] alert_id={alert_record.id} device={device_name} "
                        f"分析完成，结果长度={result_len} 已存入告警记录")

        except Exception as e:
            import traceback
            logger.warning(f"[AI根因分析] alert_id={alert_record.id} 失败（不影响告警流程）: {e}\n{traceback.format_exc()}")

    @staticmethod
    async def _send_notifications(db: AsyncSession, alert_record: AlertRecord):
        """发送告警通知"""
        # 获取规则配置的通知渠道
        query = select(AlertRule).where(AlertRule.id == alert_record.rule_id)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            logger.warning(f"[_send_notifications] alert_id={alert_record.id} rule not found (rule_id={alert_record.rule_id}), skipping")
            return
        
        channels = rule.notification_channels or []
        logger.info(f"[_send_notifications] alert_id={alert_record.id} rule={rule.id} sending to channels={channels}")
        
        for channel in channels:
            notification = AlertNotification(
                record_id=alert_record.id,
                channel=channel,
                target="",
                status="pending"
            )
            db.add(notification)
            logger.info(f"[_send_notifications] alert_id={alert_record.id} channel={channel} starting send")
            
            # 模拟发送通知
            try:
                await AlertService._send_notification(db, channel, alert_record)
                notification.status = "sent"
                notification.sent_at = datetime.now()
                logger.info(f"[_send_notifications] alert_id={alert_record.id} channel={channel} sent successfully")
            except Exception as e:
                notification.status = "failed"
                notification.error_message = str(e)
                logger.error(f"[_send_notifications] alert_id={alert_record.id} channel={channel} send failed: {e}")
    
    @staticmethod
    async def _get_notification_config(db: AsyncSession) -> dict:
        """获取通知配置"""
        result = await db.execute(select(Setting).filter(Setting.key == NOTIFICATION_SETTINGS_KEY))
        setting = result.scalars().first()
        
        config = {}
        if setting:
            try:
                config = json.loads(setting.value)
            except json.JSONDecodeError:
                pass
        
        return {
            "dingtalk_webhook_url": config.get("dingtalk_webhook_url") or settings.notification.dingtalk_webhook_url,
            "wechat_webhook_url": config.get("wechat_webhook_url") or settings.notification.wechat_webhook_url,
            "feishu_webhook_url": config.get("feishu_webhook_url") or settings.notification.feishu_webhook_url,
            "smtp_host": config.get("smtp_host") or settings.notification.smtp_host,
            "smtp_port": config.get("smtp_port") or settings.notification.smtp_port,
            "smtp_username": config.get("smtp_username") or settings.notification.smtp_username,
            "smtp_password": config.get("smtp_password") or settings.notification.smtp_password,
            "smtp_from_email": config.get("smtp_from_email") or settings.notification.smtp_from_email
        }
    
    @staticmethod
    async def _send_notification(db: AsyncSession, channel: str, alert_record: AlertRecord):
        """发送单个通知"""
        # 获取设备信息
        query = select(Device.name).where(Device.id == alert_record.device_id)
        result = await db.execute(query)
        device_name = result.scalar_one_or_none() or "未知设备"
        
        message = f"【告警】[{alert_record.severity.upper()}] {device_name}: {alert_record.message}"
        
        # 获取通知配置
        config = await AlertService._get_notification_config(db)
        
        # 根据渠道发送通知
        if channel == "dingtalk":
            await AlertService._send_dingtalk_notification(config["dingtalk_webhook_url"], message)
        elif channel == "wechat":
            await AlertService._send_wechat_notification(config["wechat_webhook_url"], message)
        elif channel == "feishu":
            await AlertService._send_feishu_notification(config["feishu_webhook_url"], message)
        elif channel == "email":
            await AlertService._send_email_notification(config, message)
        elif channel == "webhook":
            await AlertService._send_custom_webhook(message)
    
    @staticmethod
    async def _send_dingtalk_notification(webhook_url: str, message: str):
        """发送钉钉机器人通知"""
        if not webhook_url:
            logger.warning("钉钉Webhook地址未配置")
            return
        
        async with httpx.AsyncClient() as client:
            payload = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            try:
                response = await client.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"钉钉通知发送成功: {message}")
            except Exception as e:
                logger.error(f"钉钉通知发送失败: {e}")
                raise
    
    @staticmethod
    async def _send_wechat_notification(webhook_url: str, message: str):
        """发送企业微信机器人通知"""
        if not webhook_url:
            logger.warning("企业微信Webhook地址未配置")
            return

        async with httpx.AsyncClient() as client:
            payload = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            try:
                response = await client.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"企业微信通知发送成功: {message}")
            except Exception as e:
                logger.error(f"企业微信通知发送失败: {e}")
                raise
    
    @staticmethod
    async def _send_feishu_notification(webhook_url: str, message: str):
        """发送飞书机器人通知"""
        if not webhook_url:
            logger.warning("飞书Webhook地址未配置")
            return

        async with httpx.AsyncClient() as client:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": message
                }
            }
            try:
                response = await client.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"飞书通知发送成功: {message}")
            except Exception as e:
                logger.error(f"飞书通知发送失败: {e}")
                raise
    
    @staticmethod
    async def _send_email_notification(config: dict, message: str):
        """发送邮件通知"""
        smtp_host = config["smtp_host"]
        smtp_port = config["smtp_port"]
        smtp_username = config["smtp_username"]
        smtp_password = config["smtp_password"]
        smtp_from_email = config["smtp_from_email"]
        
        if not all([smtp_host, smtp_username, smtp_password, smtp_from_email]):
            logger.warning("邮件服务器配置未完整")
            return

        try:
            msg = MIMEText(message, 'plain', 'utf-8')
            msg['From'] = formataddr(('Cornerstone告警系统', smtp_from_email))
            msg['Subject'] = "【告警通知】"

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(smtp_from_email, [smtp_from_email], msg.as_string())
            logger.info(f"邮件通知发送成功: {message}")
        except Exception as e:
            logger.error(f"邮件通知发送失败: {e}")
            raise

    @staticmethod
    async def _send_custom_webhook(message: str):
        """发送自定义Webhook通知"""
        logger.info(f"自定义Webhook通知: {message}")
    
    @staticmethod
    async def acknowledge_alert(db: AsyncSession, alert_id: int, user_id: int):
        """确认告警"""
        stmt = update(AlertRecord).where(AlertRecord.id == alert_id).values(
            status="acknowledged",
            acknowledged_by=user_id,
            acknowledged_at=datetime.now()
        )
        await db.execute(stmt)
        await db.commit()
    
    @staticmethod
    async def resolve_alerts(db: AsyncSession, device_id: Optional[int] = None):
        """恢复告警（设备恢复正常时）"""
        query = select(AlertRecord).where(AlertRecord.status == "active")
        if device_id:
            query = query.where(AlertRecord.device_id == device_id)
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        for alert in alerts:
            alert.status = "resolved"
            alert.resolved_at = datetime.now()
        
        await db.commit()
    
    @staticmethod
    async def get_active_alerts(db: AsyncSession, device_id: Optional[int] = None, 
                               severity: Optional[str] = None) -> List[AlertRecord]:
        """获取活动告警"""
        query = select(AlertRecord).where(AlertRecord.status == "active")
        
        if device_id:
            query = query.where(AlertRecord.device_id == device_id)
        if severity:
            query = query.where(AlertRecord.severity == severity)
        
        query = query.order_by(AlertRecord.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_alert_summary(db: AsyncSession) -> dict:
        """获取告警统计概览"""
        query = select(
            AlertRecord.severity,
            func.count(AlertRecord.id).label("count")
        ).where(AlertRecord.status == "active").group_by(AlertRecord.severity)
        
        result = await db.execute(query)
        status_counts = result.all()
        
        summary = {"info": 0, "warning": 0, "critical": 0}
        for severity, count in status_counts:
            if severity in summary:
                summary[severity] = count
        
        return summary


alert_service = AlertService()

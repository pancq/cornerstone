# 测试 OID 匹配逻辑
oids = {
    "sys_descr": "1.3.6.1.2.1.1.1.0",
    "sys_object_id": "1.3.6.1.2.1.1.2.0",
    "sys_up_time": "1.3.6.1.2.1.1.3.0",
    "sys_name": "1.3.6.1.2.1.1.5.0",
    "sys_location": "1.3.6.1.2.1.1.6.0",
}

# 模拟 snmpget 输出
test_lines = [
    "SNMPv2-MIB::sysDescr.0 = STRING: H3C Comware Platform Software...",
    "SNMPv2-MIB::sysObjectID.0 = OID: enterprises.25506.1.1588",
    "DISMAN-EVENT-MIB::sysUpTimeInstance = Timeticks: (75273004) 8 days, 17:05:30.04",
    "SNMPv2-MIB::sysName.0 = STRING: PEK-SW-401-4-4.13",
    "SNMPv2-MIB::sysLocation.0 = STRING: Hangzhou, China",
]

oid_key_map = {v: k for k, v in oids.items()}
print("OID 映射:", oid_key_map)
print()

for line in test_lines:
    if '=' in line:
        parts = line.split('=', 1)
        if len(parts) == 2:
            oid_part = parts[0].strip()
            value = parts[1].strip().strip('"')
            
            print(f"解析行：{oid_part} = {value}")
            
            # 查找匹配的 OID
            matched = False
            for oid, key in oid_key_map.items():
                if oid in oid_part:
                    print(f"  匹配 OID: {oid} -> {key}")
                    matched = True
                    break
            
            if not matched:
                print(f"  未匹配到 OID")
            print()

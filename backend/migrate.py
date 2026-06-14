from sqlalchemy import create_engine
from sqlalchemy.sql import text

# 连接到SQLite数据库
engine = create_engine('sqlite:///./cornerstone.db')

with engine.connect() as conn:
    # 检查backup_tasks表是否有vendor字段
    result = conn.execute(text('PRAGMA table_info(backup_tasks)'))
    columns = [row[1] for row in result.fetchall()]
    print('backup_tasks columns:', columns)
    
    if 'vendor' not in columns:
        print('Adding vendor column to backup_tasks...')
        conn.execute(text('ALTER TABLE backup_tasks ADD COLUMN vendor TEXT'))
        conn.commit()
        print('Done!')
    else:
        print('vendor column already exists')
    
    # 检查devices表是否有vendor字段
    result = conn.execute(text('PRAGMA table_info(devices)'))
    columns = [row[1] for row in result.fetchall()]
    print('devices columns:', columns)
    
    if 'vendor' not in columns:
        print('Adding vendor column to devices...')
        conn.execute(text('ALTER TABLE devices ADD COLUMN vendor TEXT'))
        conn.commit()
        print('Done!')
    else:
        print('vendor column already exists')

    # 检查 vlans 表是否有 site_id 字段
    result = conn.execute(text('PRAGMA table_info(vlans)'))
    columns = [row[1] for row in result.fetchall()]
    print('vlans columns:', columns)
    
    if 'site_id' not in columns:
        print('Adding site_id column to vlans...')
        conn.execute(text('ALTER TABLE vlans ADD COLUMN site_id INTEGER'))
        conn.commit()
        print('Done!')
    else:
        print('site_id column already exists')
    
    # 创建设备连接关系表
    print('Creating device_links table...')
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS device_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_device_id INTEGER NOT NULL,
            source_interface TEXT,
            target_device_id INTEGER NOT NULL,
            target_interface TEXT,
            link_type TEXT NOT NULL DEFAULT 'manual',
            confidence INTEGER DEFAULT 100,
            discovered_at DATETIME,
            verified_at DATETIME,
            note TEXT,
            FOREIGN KEY (source_device_id) REFERENCES devices(id),
            FOREIGN KEY (target_device_id) REFERENCES devices(id)
        )
    '''))
    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_source_device ON device_links(source_device_id)'))
    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_target_device ON device_links(target_device_id)'))
    conn.commit()
    print('device_links table created!')

print('Migration completed!')

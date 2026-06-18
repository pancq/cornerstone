from src.database import sync_session
from src.models import Device, Site
with sync_session() as s:
    print('Sites:', s.query(Site).count())
    print('Devices:', s.query(Device).count())

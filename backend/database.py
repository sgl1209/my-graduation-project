from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ===================== 填写你的本地MySQL信息 =====================
DB_USER = "root"           # 你的MySQL用户名
DB_PASSWORD = "Dfs120900"   # 你的MySQL密码
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "managementdb"    # 上面创建的数据库名

# 数据库连接地址
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 创建引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 模型基类
Base = declarative_base()
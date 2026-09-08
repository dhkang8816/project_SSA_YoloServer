from pathlib import Path

basedir = Path(__file__).parent.parent

# BaseConfig 클래스를 작성한다
class BaseConfig:
    SECRET_KEY = "dkajlfdsj3dkslhl"
    WTF_CSRF_SECRET_KEY = "3hksfjlvjjwueh83"


# BaseConfig 클래스를 상속하여 LocalConfig 클래스를 작성한다
class LocalConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI= f"sqlite:///{basedir / 'local.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SQLALCHEMY_ECHO=False


# BaseConfig 클래스를 상속하여 TestingConfig 클래스를 작성한다
class TestingConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'testing.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    
# config 사전에 매핑한다
config = {
    "testing": TestingConfig,
    "local": LocalConfig,
}



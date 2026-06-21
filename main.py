from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routers.chat_router import chat_router
from client.mysql_client import init_db_engine, close_db_engine
from conf.load_env import env_config
from models.DialogueStateRecord import DialogueStateRecord  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    1.回调lifespan的时机：在服务一启动的时候会先来调用（初始化HTTP客户端、Redis客户端、MySQL数据库的连接池...）
    2.参数app以及类型必须要指定，因为底层FastAPI对资源做共享和传递
    3.yield: 让FASTAPI处理请求，等应用关闭,才执行close_db_engine
    :return:
    """
    init_db_engine()
    yield  # FASTAPI 处理请求....
    await close_db_engine()  # 应用关闭的时候才执行到


app = FastAPI(title="Ecommerce Dialogue State Backend", lifespan=lifespan)
app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=env_config['APP_HOST'], port=int(env_config['APP_PORT']), reload=True)

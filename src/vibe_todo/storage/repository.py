"""数据持久化仓储实现"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ..core.models import Task, TaskStatus, TaskPriority

Base = declarative_base()


class TaskModel(Base):
    """任务数据库模型"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), default="")
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    time_spent = Column(Integer, default=0)  # 分钟
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    # 扩展字段
    due_date = Column(DateTime, nullable=True)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    tags = Column(String(500), default="")  # 以逗号分隔
    project = Column(String(100), nullable=True)

    def to_domain(self) -> Task:
        """转换为领域模型"""
        return Task(
            task_id=self.id,
            title=self.title,
            description=self.description,
            status=self.status,
            time_spent=self.time_spent,
            created_at=self.created_at,
            updated_at=self.updated_at,
            due_date=self.due_date,
            priority=self.priority,
            tags=self.tags.split(",") if self.tags else [],
            project=self.project,
        )

    @staticmethod
    def from_domain(task: Task) -> "TaskModel":
        """从领域模型创建"""
        return TaskModel(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            time_spent=task.time_spent,
            created_at=task.created_at,
            updated_at=task.updated_at,
            due_date=task.due_date,
            priority=task.priority,
            tags=",".join(task.tags) if task.tags else "",
            project=task.project,
        )


class TaskRepository:
    """任务仓储"""

    def __init__(self, db_path: str = "vibe_todo.db"):
        """
        Args:
            db_path: 数据库文件路径
        """
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def save(self, task: Task) -> Task:
        """保存或更新任务"""
        session = self._get_session()
        try:
            if task.id:
                # 更新现有任务
                db_task = session.query(TaskModel).filter(TaskModel.id == task.id).first()
                if db_task:
                    db_task.title = task.title
                    db_task.description = task.description
                    db_task.status = task.status
                    db_task.time_spent = task.time_spent
                    db_task.updated_at = task.updated_at
                    db_task.due_date = task.due_date
                    db_task.priority = task.priority
                    db_task.tags = ",".join(task.tags) if task.tags else ""
                    db_task.project = task.project
                else:
                    db_task = TaskModel.from_domain(task)
                    session.add(db_task)
            else:
                # 创建新任务
                db_task = TaskModel.from_domain(task)
                session.add(db_task)

            session.commit()
            session.refresh(db_task)
            return db_task.to_domain()
        finally:
            session.close()

    def get_by_id(self, task_id: int) -> Optional[Task]:
        """根据 ID 获取任务"""
        session = self._get_session()
        try:
            db_task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            return db_task.to_domain() if db_task else None
        finally:
            session.close()

    def list_all(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """列出所有任务，可按状态筛选"""
        session = self._get_session()
        try:
            query = session.query(TaskModel)
            if status:
                query = query.filter(TaskModel.status == status)
            db_tasks = query.order_by(TaskModel.created_at.desc()).all()
            return [db_task.to_domain() for db_task in db_tasks]
        finally:
            session.close()

    def delete(self, task_id: int) -> bool:
        """删除任务"""
        session = self._get_session()
        try:
            db_task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                session.delete(db_task)
                session.commit()
                return True
            return False
        finally:
            session.close()

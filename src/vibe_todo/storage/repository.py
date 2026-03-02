"""数据持久化仓储实现"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, Integer, String, create_engine, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ..adapters import TaskFilter, TaskRepositoryInterface
from ..core.models import Task, TaskPriority, TaskStatus

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


class TaskRepository(TaskRepositoryInterface):
    """任务仓储"""

    def __init__(self, db_path: str = "vibe_todo.db"):
        """
        Args:
            db_path: 数据库文件路径
        """
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self._create_fts_table()
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _create_fts_table(self):
        """创建 FTS5 全文搜索虚拟表"""
        with self.engine.connect() as conn:
            # 检查 FTS5 支持
            result = conn.execute(text("SELECT sqlite_version()"))
            version = result.fetchone()[0]

            # 创建 FTS5 虚拟表
            conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS tasks_fts 
                USING fts5(
                    title, 
                    description, 
                    tags, 
                    project,
                    content=tasks,
                    content_rowid=id
                )
            """))

            # 创建触发器以保持 FTS 表同步
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS tasks_ai AFTER INSERT ON tasks
                BEGIN
                    INSERT INTO tasks_fts(rowid, title, description, tags, project)
                    VALUES (new.id, new.title, new.description, new.tags, new.project);
                END;
            """))

            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS tasks_ad AFTER DELETE ON tasks
                BEGIN
                    INSERT INTO tasks_fts(tasks_fts, rowid, title, description, tags, project)
                    VALUES ('delete', old.id, old.title, old.description, old.tags, old.project);
                END;
            """))

            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS tasks_au AFTER UPDATE ON tasks
                BEGIN
                    INSERT INTO tasks_fts(tasks_fts, rowid, title, description, tags, project)
                    VALUES ('delete', old.id, old.title, old.description, old.tags, old.project);
                    INSERT INTO tasks_fts(rowid, title, description, tags, project)
                    VALUES (new.id, new.title, new.description, new.tags, new.project);
                END;
            """))

            conn.commit()

            # 初始填充 FTS 表（如果已有数据）
            conn.execute(text("""
                INSERT OR REPLACE INTO tasks_fts(rowid, title, description, tags, project)
                SELECT id, title, description, tags, project FROM tasks
            """))
            conn.commit()

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

    def search(self, query: str) -> List[Task]:
        """全文搜索任务（使用 FTS5）
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的任务列表，按相关性排序
        """
        session = self._get_session()
        try:
            # 使用 FTS5 搜索
            sql = text("""
                SELECT t.* FROM tasks t
                INNER JOIN tasks_fts fts ON t.id = fts.rowid
                WHERE tasks_fts MATCH :query
                ORDER BY rank
            """)
            result = session.execute(sql, {"query": query})
            db_tasks = []
            for row in result:
                # 通过 ORM 查询获取完整的 TaskModel 对象
                db_task = session.query(TaskModel).filter(TaskModel.id == row.id).first()
                if db_task:
                    db_tasks.append(db_task)

            # 如果 FTS 搜索没有结果，回退到简单的 LIKE 搜索
            if not db_tasks:
                query_lower = f"%{query.lower()}%"
                db_tasks = session.query(TaskModel).filter(
                    (TaskModel.title.ilike(query_lower)) |
                    (TaskModel.description.ilike(query_lower)) |
                    (TaskModel.tags.ilike(query_lower)) |
                    (TaskModel.project.ilike(query_lower))
                ).all()

            return [db_task.to_domain() for db_task in db_tasks]
        except Exception:
            # 如果 FTS 出错，回退到默认实现
            return super().search(query)
        finally:
            session.close()

    def filter_tasks(self, task_filter: TaskFilter) -> List[Task]:
        """高级过滤任务（SQLite 优化实现）
        
        Args:
            task_filter: 过滤条件
            
        Returns:
            符合条件的任务列表
        """
        if not task_filter.has_any_filter():
            return self.list_all()

        session = self._get_session()
        try:
            query = session.query(TaskModel)

            if task_filter.status:
                query = query.filter(TaskModel.status == task_filter.status)

            if task_filter.priority:
                query = query.filter(TaskModel.priority == task_filter.priority)

            if task_filter.project:
                query = query.filter(TaskModel.project == task_filter.project)

            if task_filter.tags:
                if task_filter.tags_operator == "AND":
                    for tag in task_filter.tags:
                        query = query.filter(TaskModel.tags.contains(tag))
                else:
                    from sqlalchemy import or_
                    tag_filters = [TaskModel.tags.contains(tag) for tag in task_filter.tags]
                    query = query.filter(or_(*tag_filters))

            db_tasks = query.order_by(TaskModel.created_at.desc()).all()
            tasks = [db_task.to_domain() for db_task in db_tasks]

            # 内存过滤（处理需要 Python 逻辑的条件）
            if task_filter.overdue_only:
                tasks = [t for t in tasks if t.is_overdue()]

            if task_filter.due_in_days is not None:
                tasks = [
                    t for t in tasks
                    if t.due_date and t.days_until_due() is not None
                    and 0 <= t.days_until_due() <= task_filter.due_in_days
                ]

            return tasks
        finally:
            session.close()

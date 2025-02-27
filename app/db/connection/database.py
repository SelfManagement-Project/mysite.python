from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from config.env.database import DATABASE_URL

# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# automap 설정
Base = automap_base()
Base.prepare(autoload_with=engine)

# 기존 테이블에 매핑된 클래스 - 모든 테이블 추가
User = Base.classes.user
ChatHistory = Base.classes.chat_history
Documents = Base.classes.documents
Alert = Base.classes.alert
Budget = Base.classes.budget
BudgetAlert = Base.classes.budget_alert
CategoryBudget = Base.classes.category_budget
Chat = Base.classes.chat
Diet = Base.classes.diet
Exercise = Base.classes.exercise
Facility = Base.classes.facility
FinanceCategory = Base.classes.finance_category
Habit = Base.classes.habit
HabitLog = Base.classes.habit_log
HealthMetrics = Base.classes.health_metrics
SavingsGoal = Base.classes.savings_goal
Schedule = Base.classes.schedule
Sleep = Base.classes.sleep
SpringSession = Base.classes.spring_session
SpringSessionAttributes = Base.classes.spring_session_attributes
Transaction = Base.classes.transaction

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 세션 생성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from sqlalchemy import create_engine, Column, Integer, DateTime,String, Float, ForeignKey,Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from databases import Database
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import timedelta, datetime
from sqlalchemy.sql import text


DATABASE_URL = "postgresql+psycopg2://parking:passwordpsql@localhost/dbparking"

database = Database(DATABASE_URL)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

class ResetToken(Base):
    __tablename__ = 'reset_token'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    token = Column(String, unique=True)
    expires_at = Column(DateTime, server_default=text('(now() + interval \'30 minutes\')'))


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), index=True)
    email = Column(String(255))
    last_connection = Column(DateTime(timezone=True), server_default=func.now())
    created_date = Column(DateTime(timezone=True), server_default=func.now())  # Add this field
    cars = relationship("Car", back_populates="user")
    hashed_password = Column(String(255))  # Add this field for hashed passwords
    parking_movements = relationship("ParkingMovement", back_populates="user")
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True) 


class Wallet(Base):
    __tablename__ = "wallet"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    balance = Column(Float)

class Car(Base):
    __tablename__ = "car"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    license_plate = Column(String(255))
    year = Column(Integer)  # Add the year field
    brand = Column(String(255))  # Add the brand field
    model = Column(String(255))  # Add the model field

    # Establish a many-to-one relationship with users
    user = relationship("User", back_populates="cars")
    is_active = Column(Boolean,default='true')
    in_use = Column(Boolean,default='false')



class ParkingMovement(Base):
    __tablename__ = "parking_movement"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    parking_spot_id = Column(String)
    total_cost = Column(Float)
    # Additional attributes
    vehicle_type = Column(String)
    license_plate = Column(String)
    notes = Column(String)

    # Define relationships
    user = relationship("User", back_populates="parking_movements")


class Reservation(Base):
    __tablename__ = "reservation"

    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    parking_spot_id = Column(String)  
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    user = relationship("User", back_populates="reservations")
    # parking_spot = relationship("ParkingSpot", back_populates="reservations") # Descomenta esto si tienes una tabla de ParkingSpot

# Agrega la relación en la clase User
    User.reservations = relationship("Reservation", back_populates="user")
# ParkingSpot.reservations = relationship("Reservation", back_populates="parking_spot") # Descomenta esto si tienes una tabla de ParkingSpot



engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def connect_to_db():
    await database.connect()

async def disconnect_from_db():
    await database.disconnect()

def fetch_user_from_db(username: str, session: Session):
    return session.query(User).filter(User.username == username).first()

async def get_car(db: Session, car_id: int):
    return db.query(Car).filter(Car.id == car_id).first()

async def get_parking_history_for_car(db: Session, car_id: int):
    return db.query(ParkingHistory).filter(ParkingHistory.car_id == car_id).all()


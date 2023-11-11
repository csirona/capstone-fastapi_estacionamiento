from fastapi import FastAPI, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from db import connect_to_db, disconnect_from_db, SessionLocal, User, Wallet, Card, Car, fetch_user_from_db, ParkingHistory, get_car, ResetToken, ParkingMovement,Reservation
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from db import SessionLocal
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta, timezone
from transbank.webpay.webpay_plus.transaction import Transaction as WebpayTransaction
from fastapi.responses import HTMLResponse
from fastapi import Request
from transbank.error.transbank_error import TransbankError



app = FastAPI()

origins = ["*"]  # Add your frontend URLs

# JWT configuration
SECRET_KEY = "9a906627c7d4dac428f7ca952626b15e4cae78aa8f784527637f46ed5aba1eaa"
ALGORITHM = "HS512"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Function to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for creating a user
class UserCreate(BaseModel):
    username: str
    email: str
    hashed_password: str
    role: str
    is_active: Optional[bool] = True

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Pydantic model for creating a wallet
class WalletCreate(BaseModel):
    user_id: int
    balance: float

# Pydantic model for wallet response
class WalletResponse(BaseModel):
    id: int
    user_id: int
    balance: float

# Pydantic model for creating a card
class CardCreate(BaseModel):
    user_id: int
    card_number: str

# Pydantic model for card response
class CardResponse(BaseModel):
    id: int
    user_id: int
    card_number: str

# Pydantic model for creating a car
class CarCreate(BaseModel):
    user_id: int
    license_plate: str
    year: int  
    brand: str 
    model: str
    is_active: bool

# Pydantic model for car response
class CarResponse(BaseModel):
    id: int
    user_id: int
    license_plate: str
    year: int  
    brand: str 
    model: str
    is_active: bool


# Pydantic model for user response
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    hashed_password: str
    last_connection: Optional[datetime]
    created_date: Optional[datetime]
    role: Optional[str]
    is_active: bool


class ParkingMovementCreate(BaseModel):
    user_id: int
    entry_time: str  # Change to string
    exit_time: Optional[str]  # Change to string, as it's optional
    parking_spot_id: int
    total_cost: float
    vehicle_type: str
    license_plate: str
    notes: str

class ParkingMovementResponse(BaseModel):
    id: int
    user_id: int
    entry_time: str
    exit_time: str
    parking_spot_id: int
    total_cost: float
    vehicle_type: str
    license_plate: str
    notes: str


# class ResetToken(BaseModel):
#     email: str
#     token: str
#     expires_at: datetime

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: bool

class UserActivation(BaseModel):
    is_active: bool

# Pydantic model for creating a reservation
class ReservationCreate(BaseModel):
    id:int
    user_id: int
    parking_spot_id: str
    start_time: datetime
    end_time: datetime
    is_active: bool

# Pydantic model for reservation response
class ReservationResponse(BaseModel):
    id: int
    user_id: int
    parking_spot_id: str
    start_time: datetime
    end_time: datetime
    is_active: bool


class CarStatus(BaseModel):
    is_active: bool

# Define a Pydantic model to represent the request data for money deduction
class DeductMoneyRequest(BaseModel):
    user_id: int
    amount: float

# Define a Pydantic model to represent the payment request data
class PaymentRequest(BaseModel):
    amount: float
    currency: str
    order_info: str


@app.post("/cars/{car_id}/toggle/")
def toggle_car_status(car_id: int, car_status: CarStatus, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    car.is_active = car_status.is_active
    db.commit()
    return {"message": f"Car has been {'activated' if car_status.is_active else 'deactivated'}"}

# User authentication
def authenticate_user(db_user: User, password: str):
    if not pwd_context.verify(password, db_user.hashed_password):
        return False
    return True

# Create a JWT token with "iat" claim
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})  # Add "iat" claim
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Function to get the current user based on the JWT token
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Fetch user from the database based on the username and return it
        db_user = fetch_user_from_db(username)  # Implement this function
        if db_user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return db_user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")


@app.put("/users/{user_id}/activate")
async def activate_user(user_id: int, user_activation: UserActivation, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = user_activation.is_active
    db.commit()

    if user_activation.is_active:
        return {"message": "User activated successfully"}
    else:
        return {"message": "User deactivated successfully"}
# Login route
@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username
    password = form_data.password
    db_user = fetch_user_from_db(username, db)  # Pass the session as well
    
    if db_user and db_user.is_active and pwd_context.verify(password, db_user.hashed_password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username,"user_id": db_user.id}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

# Login admin route
@app.post("/login-admin", response_model=Token)
async def login_admin_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username
    password = form_data.password
    db_user = fetch_user_from_db(username, db)  # Pass the session as well
    
    if db_user and pwd_context.verify(password, db_user.hashed_password) and db_user.role=='admin':
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username,"user_id": db_user.id}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


def generate_reset_token():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))



def save_reset_token(email, token, expires_at, db):
    reset_token = ResetToken(email=email, token=token, expires_at=expires_at)
    db.add(reset_token)
    db.commit()



# Function to send a password reset email
def send_reset_email(email, token):
    # SMTP configuration
    smtp_host = 'fastserver.cimaspeed.com'
    smtp_port = 587
    smtp_secure = False
    smtp_user = 'automotrizmarweg@grafibook.cl'
    smtp_pass = 'marweg'

    # Create an SMTP connection
    smtp_server = smtplib.SMTP(host=smtp_host, port=smtp_port)
    smtp_server.starttls()
    smtp_server.login(smtp_user, smtp_pass)

    # Email content
    sender_email = 'automotrizmarweg@grafibook.cl'
    subject = 'Password Reset'

    # HTML content for the email
    html_content = f"""
    <html>
      <body>
        <div style="font-family: Arial, sans-serif; background-color: #f2f2f2; padding: 20px;">
          <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
            <h1 style="color: #0070C0;">Restablecimiento de Contraseña</h1>
            <p>Hola,</p>
            <p>Este es tu código de restablecimiento de contraseña:</p>
            <p><strong>Token: {token}</strong></p>
          </div>
        </div>
      </body>
    </html>
    """

    # Create an email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject

    # Attach the HTML content to the email
    msg.attach(MIMEText(html_content, 'html'))

    # Send the email
    try:
        smtp_server.sendmail(sender_email, email, msg.as_string())
        print('Password reset email sent successfully')
    except Exception as e:
        print('Error sending email:', str(e))

    # Close the SMTP connection
    smtp_server.quit()

@app.post("/reset-password/")
async def reset_password(username: str, db: Session = Depends(get_db)):
    user = fetch_user_from_db(username, db)
    if user:
        # Generate a random reset token
        token = generate_reset_token()

        # Calculate the expiration time (e.g., 30 minutes from the current time)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        email = user.email  # Move this line inside the if block

        # Save the token in the database (expiration time is set by the model)
        save_reset_token(email, token, expires_at, db)

        # Send an email to the user with a link including the reset token
        send_reset_email(email, token)

        return {"message": "Password reset link sent to your email."}
    else:
        raise HTTPException(status_code=404, detail="User not found")


def validate_reset_token(token: str, email: str, db: Session):
    # Query the database to find the reset token
    reset_token = db.query(ResetToken).filter(
        ResetToken.token == token,
        ResetToken.email == email
    ).first()

    # Check if the token exists and whether it has expired
    if reset_token and reset_token.expires_at > datetime.now(timezone.utc):
        # Token is valid, return the associated email
        return reset_token.email
    else:
        # Token is not valid, return None
        return None
    
def hash_password(password: str) -> str:
    # Hash the provided password
    return pwd_context.hash(password)

def update_user_password(email: str, hashed_password: str, db: Session):
    # Query the user by email
    user = db.query(User).filter(User.email == email).first()

    if user:
        # Update the user's hashed password
        user.hashed_password = hashed_password
        db.commit()
    else:
        # Handle the case where the user is not found
        # You can choose to raise an exception or return an error message
        raise ValueError("User not found")
    
@app.post("/reset-password/{token}")
async def reset_password(token: str,email:str, new_password: str, db: Session = Depends(get_db)):
    email = validate_reset_token(token,email, db)
    if email:
        # Hash the new password
        hashed_password = hash_password(new_password)

        # Update the user's password in the database
        update_user_password(email, hashed_password, db)

        return {"message": "Password reset successfully."}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")


# Protected resource
@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": "This is a protected resource"}

@app.on_event("startup")
async def startup():
    await connect_to_db()

@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_db()

@app.get("/cars/{user_id}", response_model=List[CarResponse])
async def get_cars(user_id: int):
    db = SessionLocal()
    cars = db.query(Car).filter(Car.user_id == user_id).all()
    db.close()


    car_responses = []
    for car in cars:
        car_response = CarResponse(
            id=car.id,
            user_id=car.user_id,
            license_plate=car.license_plate,
            year=car.year,
            brand=car.brand,
            model=car.model,
            is_active=car.is_active
        )
        car_responses.append(car_response)

    return car_responses

from fastapi import HTTPException

@app.get("/cars/{car_id}", response_model=CarResponse)
async def get_car_id(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    car_response = CarResponse(
        id=car.id,
        user_id=car.user_id,
        license_plate=car.license_plate,
        year=car.year,
        brand=car.brand,
        model=car.model,
        is_active=car.is_active
    )

    return car_response

    
# Add a route to list all users
@app.get("/users/", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    db.close()
    user_responses = []
    for user in users:
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            last_connection = user.last_connection if user.last_connection else None,
            created_date=user.created_date,
            role=user.role,
            is_active=user.is_active,
        )
        user_responses.append(user_response)
    return user_responses


# Get a user by ID
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        hashed_password=user.hashed_password,
        last_connection=user.last_connection if user.last_connection else None,
        created_date=user.created_date,
        role=user.role,
        is_active=user.is_active
    )

# Get a user by username
@app.get("/users/by-username/{username}", response_model=UserResponse)
async def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        hashed_password=user.hashed_password,
        last_connection=user.last_connection if user.last_connection else None,
        created_date=user.created_date,
        role=user.role,
        is_active=user.is_active
    )

@app.post("/users/", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Hash the provided password
    hashed_password = hash_password(user_data.hashed_password)

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=user_data.is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        hashed_password=user.hashed_password,
        last_connection=None,
        created_date=user.created_date,
        role=user.role,
        is_active=user.is_active
    )
# Update a user by ID
@app.put("/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Flag to check if any updates were made
    updated = False
    
    # Update the user details
    if user_data.username:
        user.username = user_data.username
        updated = True
    if user_data.email:
        user.email = user_data.email
        updated = True
    
    if updated:

        db.commit()
        return {"message": "User updated successfully"}
    else:
        return {"message": "No updates provided"}


# Delete a user by ID
@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}   


# Pydantic model for updating user email
class UpdateUserEmail(BaseModel):
    new_email: str

# Endpoint to modify user email
@app.put("/users/{user_id}/update-email")
async def update_user_email(user_id: int, update_data: UpdateUserEmail, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email = update_data.new_email
    db.commit()

    return {"message": "User email updated successfully"}


# Pydantic model for updating car details
class UpdateCarDetails(BaseModel):
    license_plate: Optional[str] = None
    year: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    is_active: Optional[bool] = None

# Endpoint to modify car details
@app.put("/cars/{car_id}/update-details")
async def update_car_details(car_id: int, update_data: UpdateCarDetails, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # Update car details if provided in the request
    if update_data.license_plate is not None:
        car.license_plate = update_data.license_plate
    if update_data.year is not None:
        car.year = update_data.year
    if update_data.brand is not None:
        car.brand = update_data.brand
    if update_data.model is not None:
        car.model = update_data.model
    if update_data.is_active is not None:
        car.is_active = update_data.is_active

    db.commit()

    return {"message": "Car details updated successfully"}



# Create a new wallet
@app.post("/wallets/")
async def create_wallet(wallet_data: WalletCreate):
    try:
        db = SessionLocal()
        new_wallet = Wallet(user_id=wallet_data.user_id, balance=wallet_data.balance)
        db.add(new_wallet)
        db.commit()
        db.close()
        return {"message": "Wallet created successfully"}
    except Exception as e:
        return {"message": f"Error creating wallet: {str(e)}"}


@app.get("/wallets/", response_model=List[WalletResponse])
async def list_wallets(db: Session = Depends(get_db)):
    wallets = db.query(Wallet).all()
    wallet_responses = []
    for wallet in wallets:
        wallet_response = WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            balance=wallet.balance
        )
        wallet_responses.append(wallet_response)
    return wallet_responses


# Get a wallet by ID
@app.get("/wallets/{user_id}")
async def get_wallet(user_id: int):
    db = SessionLocal()
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    db.close()
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet



@app.post("/wallet/charge/{user_id}")
async def charge_wallet(user_id: int, amount: float, db: Session = Depends(get_db)):
    # Retrieve the user's wallet
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Update the wallet balance
    wallet.balance += amount
    db.commit()

    # Return the updated wallet information
    return WalletResponse(id=wallet.id, user_id=wallet.user_id, balance=wallet.balance)

# Simulate payment initiation (replace this with actual integration)
@app.post("/initiate-payment/")
async def initiate_payment(payment_request: PaymentRequest):
    # Extract payment details from the request
    amount = payment_request.amount
    currency = payment_request.currency
    order_info = payment_request.order_info

    # Simulate payment initiation
    simulated_payment_url = f"https://webpay-chile.com/payment?amount={amount}&currency={currency}&order_info={order_info}"

    return {"message": "Payment initiated successfully (simulated)", "redirect_url": simulated_payment_url}

@app.post("/deduct-money/")
async def deduct_money(request_data: DeductMoneyRequest, db: Session = Depends(get_db)):
    user_id = request_data.user_id
    amount =request_data.amount

    try:
        # Check if the user has an active reservation
        #active_reservation = db.query(Reservation).filter(Reservation.user_id == user_id, Reservation.is_active == True).first()

        if True:#active_reservation:
            # User has an active reservation, deduct the money from their wallet
            user = db.query(User).filter(User.id == user_id).first()
            wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()

            if not wallet or wallet.balance <= 0:
                raise HTTPException(status_code=400, detail="Insufficient balance")

            wallet.balance -= amount  # Deduct one unit of currency from the wallet
            db.commit()

            return {"message": "Money deducted successfully"}
        else:
            raise HTTPException(status_code=400, detail="No active reservation found")
    except Exception as e:
        # Handle any exceptions here and optionally roll back the transaction if needed
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

@app.post("/cards/")
async def create_card(card_data: CardCreate):
    db = SessionLocal()
    new_card = Card(user_id=card_data.user_id, card_number=card_data.card_number)
    db.add(new_card)
    db.commit()
    db.close()
    return {"message": "Card created successfully"}

# Get a card by ID
@app.get("/cards/{card_id}")
async def get_card(card_id: int):
    db = SessionLocal()
    card = db.query(Card).filter(Card.id == card_id).first()
    db.close()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    return card

@app.post("/cars/", response_model=CarResponse)
async def create_car(car_data: CarCreate):
    try:
        db = SessionLocal()
        new_car = Car(
            user_id=car_data.user_id,
            license_plate=car_data.license_plate,
            year=car_data.year,
            brand=car_data.brand,
            model=car_data.model,
            is_active=car_data.is_active,
        )
        db.add(new_car)
        db.commit()
        db.refresh(new_car)
        db.close()
        return new_car  # Return the newly created car
    except Exception as e:
        return {"message": f"Error creating car: {str(e)}"}





class ParkingHistoryCreate(BaseModel):
    car_id: int

class ParkingHistoryResponse(BaseModel):
    id: int
    date: Optional[datetime]

@app.post("/parking-history/", response_model=Dict[str, str])
async def create_parking_history(parking_history_data: ParkingHistoryCreate, response: Response):
    db = SessionLocal()
    try:
        car = db.query(Car).filter(Car.id == parking_history_data.car_id).first()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

        new_parking_history = ParkingHistory(car_id=parking_history_data.car_id)
        db.add(new_parking_history)
        db.commit()
        db.refresh(new_parking_history)

        return {"message": "Parking history entry created successfully"}

    except Exception as e:
        response.status_code = 500
        return {"message": f"Error creating parking history: {str(e)}"}
    finally:
        db.close()

@app.get("/parking-history/{car_id}", response_model=List[ParkingHistoryResponse])
async def get_parking_history(car_id: int):
    db = SessionLocal()
    try:
        car = db.query(Car).filter(Car.id == car_id).first()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

        parking_history = db.query(ParkingHistory).filter(ParkingHistory.car_id == car_id).all()
        return [{"id": entry.id, "date": entry.date} for entry in parking_history]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching parking history: {str(e)}")
    finally:
        db.close()

class CheckExistenceRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

        
@app.post("/users/check-existence")
async def check_existence(request_data: CheckExistenceRequest, db: Session = Depends(get_db)):
    if request_data.username:
        user_by_username = db.query(User).filter(User.username == request_data.username).first()
        if user_by_username:
            return {"exists": True, "type": "username"}
    if request_data.email:
        user_by_email = db.query(User).filter(User.email == request_data.email).first()
        if user_by_email:
            return {"exists": True, "type": "email"}

    return {"exists": False, "type": None}

# Create a new parking movement

# Create a new parking movement
@app.post("/parking-movements/", response_model=ParkingMovementResponse)
async def create_parking_movement(parking_movement_data: ParkingMovementCreate):
    try:
        db = SessionLocal()

        # Convert entry_time and exit_time from strings to datetime objects
        entry_time = datetime.fromisoformat(parking_movement_data.entry_time)
        exit_time = datetime.fromisoformat(parking_movement_data.exit_time) if parking_movement_data.exit_time else None

        # Create a new parking movement
        new_parking_movement = ParkingMovement(
            user_id=parking_movement_data.user_id,
            entry_time=entry_time,
            exit_time=exit_time,
            parking_spot_id=parking_movement_data.parking_spot_id,
            total_cost=parking_movement_data.total_cost,
            vehicle_type=parking_movement_data.vehicle_type,
            license_plate=parking_movement_data.license_plate,
            notes=parking_movement_data.notes,
        )

        db.add(new_parking_movement)
        db.commit()
        db.refresh(new_parking_movement)

        db.close()

        # Convert entry_time and exit_time to strings for the response
        entry_time_str = str(new_parking_movement.entry_time)
        exit_time_str = str(new_parking_movement.exit_time) if new_parking_movement.exit_time else None

        # Create the response
        parking_movement_response = ParkingMovementResponse(
            id=new_parking_movement.id,
            user_id=new_parking_movement.user_id,
            entry_time=entry_time_str,
            exit_time=exit_time_str,
            parking_spot_id=new_parking_movement.parking_spot_id,
            total_cost=new_parking_movement.total_cost,
            vehicle_type=new_parking_movement.vehicle_type,
            license_plate=new_parking_movement.license_plate,
            notes=new_parking_movement.notes,
        )

        return parking_movement_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating parking movement: {str(e)}")


# Get parking movements for a user
@app.get("/parking-movements/{user_id}", response_model=List[ParkingMovementResponse])
async def get_parking_movements(user_id: int):
    try:
        db = SessionLocal()
        
        parking_movements = db.query(ParkingMovement).filter(ParkingMovement.user_id == user_id).all()
        db.close()

        parking_movement_responses = []
        for parking_movement in parking_movements:
            parking_movement_response = ParkingMovementResponse(
                id=parking_movement.id,
                user_id=parking_movement.user_id,
                entry_time=str(parking_movement.entry_time),  # Convert to string
                exit_time=str(parking_movement.exit_time),  # Convert to string
                parking_spot_id=parking_movement.parking_spot_id,
                total_cost=parking_movement.total_cost,
                vehicle_type=parking_movement.vehicle_type,
                license_plate=parking_movement.license_plate,
                notes=parking_movement.notes,
            )
            parking_movement_responses.append(parking_movement_response)

        return parking_movement_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching parking movements: {str(e)}")

# Create a reservation
@app.post("/reservations/", response_model=ReservationResponse)
def create_reservation(reservation: ReservationCreate, db: Session = Depends(get_db)):
    db_reservation = Reservation(**reservation.dict())
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

# Read a reservation
@app.get("/reservations/{reservation_id}", response_model=ReservationResponse)
def read_reservation(reservation_id: str, db: Session = Depends(get_db)):
    db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return db_reservation

# Cancel a reservation
@app.put("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: str, db: Session = Depends(get_db)):
    db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    db_reservation.is_active = False
    db.commit()
    return {"status": "Reservation cancelled"}

# Get reservations by user ID
@app.get("/reservations/user/{user_id}", response_model=List[ReservationResponse])
def get_reservations_by_user_id(user_id: int, db: Session = Depends(get_db)):
    db_reservations = db.query(Reservation).filter(Reservation.user_id == user_id).all()
    if not db_reservations:
        raise HTTPException(status_code=404, detail="No reservations found for the user")
    return db_reservations

# Get all reservations
@app.get("/reservations/all", response_model=List[ReservationResponse])
def get_all_reservations(db: Session = Depends(get_db)):
    db_reservations = db.query(Reservation).all()
    if not db_reservations:
        return []  # Return an empty list if there are no reservations
    return db_reservations




class ReservationTimeRange(BaseModel):
    start_time: datetime
    end_time: datetime

@app.post("/reservations/check")
def check_reservation_in_range(spot_id: str, range_data: ReservationTimeRange, db: Session = Depends(get_db)):
    active_reservations = db.query(Reservation).filter(
        Reservation.parking_spot_id == spot_id,
        Reservation.start_time < range_data.end_time,
        Reservation.end_time > range_data.start_time,
        Reservation.is_active == True
    ).all()
    
    if active_reservations:
        return {"status": "Unavailable", "reservations": [{"start_time": res.start_time, "end_time": res.end_time} for res in active_reservations]}
    else:
        return {"status": "Available"}




# Pydantic model for creating a Webpay transaction
class WebpayCreateRequest(BaseModel):
    buy_order: str
    session_id: str
    amount: int
    return_url: str

# Route to create a Webpay transaction
@app.post("/webpay-plus/create", response_model=dict)
async def webpay_plus_create(request_data: WebpayCreateRequest, db: Session = Depends(get_db)):
    try:
        print("Webpay Plus Transaction.create")

        # Extract data from the request
        buy_order = request_data.buy_order
        session_id = request_data.session_id
        amount = request_data.amount
        return_url = request_data.return_url

        # Create the transaction request
        create_request = {
            "buy_order": buy_order,
            "session_id": session_id,
            "amount": amount,
            "return_url": return_url
        }

        # Call Transbank's Webpay create method
        response = WebpayTransaction().create(buy_order, session_id, amount, return_url)

        print(response)

        return {"request": create_request, "response": response}
    except TransbankError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to handle Webpay commit
@app.post("/webpay-plus/commit", response_model=dict)
async def webpay_plus_commit(token_ws: str, db: Session = Depends(get_db)):
    try:
        print("commit for token_ws: {}".format(token_ws))

        # Commit the Webpay transaction using the received token
        response = WebpayTransaction().commit(token=token_ws)
        print("response: {}".format(response))

        return {"token": token_ws, "response": response}
    except TransbankError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to handle Webpay commit error
@app.post("/webpay-plus/commit-error", response_model=dict)
async def webpay_plus_commit_error(token_ws: str, db: Session = Depends(get_db)):
    try:
        print("commit error for token_ws: {}".format(token_ws))

        # Simulate an error in the commit process
        response = {
            "error": "Transacción con errores"
        }

        return {"token": token_ws, "response": response}
    except TransbankError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to handle Webpay refund
@app.post("/webpay-plus/refund", response_model=dict)
async def webpay_plus_refund(token_ws: str, amount: float, db: Session = Depends(get_db)):
    try:
        print("refund for token_ws: {} by amount: {}".format(token_ws, amount))

        # Refund the Webpay transaction using the received token and amount
        response = WebpayTransaction().refund(token_ws, amount)
        print("response: {}".format(response))

        return {"token": token_ws, "amount": amount, "response": response}
    except TransbankError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to render the Webpay refund form
@app.get("/webpay-plus/refund-form", response_class=HTMLResponse)
async def webpay_plus_refund_form(request: Request):
    return templates.TemplateResponse("webpay/plus/refund-form.html", {"request": request})



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Pets, PetSub, User
from sqlalchemy.orm import scoped_session
from flask import session as login_session

engine = create_engine('sqlite:///petadopt.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = scoped_session(DBSession)

user1 = User(
    name='Miller',
    email='dskaran55@gmail.com',
    img_url='https://img.com/sdf'
)

session.add(user1)
session.commit()

pets1 = Pets(
    category='Dogs',
    img_url='https://i.ibb.co/568zQd0/xx.jpg',
    user=user1
)

session.add(pets1)
session.commit()

item1 = PetSub(
    breed="German Shepherd",
    contact=904415788856,
    description="Availble for adoption. He's 3 years old as of now.",
    gender="M",
    img_url="https://i.ibb.co/3rkbPLP/GSD-Standing-GSC-600x425.jpg",
    location="Lucknow, India",
    medical_record_info="Healthy",
    name="Mack",
    owner="Karan",
    pets=pets1,
    user=user1
)

session.add(item1)
session.commit()

print('Items added successfully!')

from datetime import datetime
import HarryBotter as HB

def addHouses():
    house1 = HB.House('Hufflepuff')
    house2 = HB.House('Ravenclaw')
    house3 = HB.House('Gryffindor')
    house4 = HB.House('Slytherin')
    db.session.add(house1)
    db.session.add(house2)
    db.session.add(house3)
    db.session.add(house4)
    db.session.commit()

# Has to use user_id since user might not exist
def user_exists(db,user_id):
    user = HB.User.query.filter_by(user_id=user_id).first()
    if user is None:
        print user_id
        user = HB.User(user_id)
        db.session.add(user)
        db.session.commit()
        # create_user(users, user_id, user_fb)
        return user
    return user

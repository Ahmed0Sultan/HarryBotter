from datetime import datetime
import HarryBotter as HB

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

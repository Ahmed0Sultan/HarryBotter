from datetime import datetime
import HarryBotter as HB

# Has to use user_id since user might not exist
def user_exists(db,users, user_id):
    user = users.find_one({'user_id': user_id})
    if user is None:
        print user_id
        user = HB.User(user_id)
        db.session.add(user)
        db.session.commit()
        # create_user(users, user_id, user_fb)
        return False
    return True

# Has to use user_id since user has not existed
def create_user(users, user_id, user_fb):
    timestamp = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
    user_insert = {'user_id': user_id,
                    'created_at': timestamp,

                }
    users.insert(user_insert)
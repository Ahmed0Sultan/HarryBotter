from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), unique=True)
    house = db.Column(db.String(120))
    q1 = db.Column(db.String(80))
    q2 = db.Column(db.String(80))
    q3 = db.Column(db.String(80))
    q4 = db.Column(db.String(80))
    q5 = db.Column(db.String(80))
    created_at = db.Column(db.DateTime)

    def __init__(self, user_id):
        self.user_id = user_id
        self.created_at = datetime.utcnow()

    def get_q1(self):
        return self.q1

    def get_q2(self):
        return self.q2

    def get_q3(self):
        return self.q3

    def get_q4(self):
        return self.q4

    def get_q5(self):
        return self.q5

    def get_house(self):
        return self.house

# Has to use user_id since user might not exist
def user_exists(db,users, user_id):
    user = users.find_one({'user_id': user_id})
    if user is None:
        print user_id
        user = User(user_id)
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
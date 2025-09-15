# 판독시 사용 상수
LEFT_EYE: int = 0
RIGHT_EYE: int = 1
UNRECOGNIZABLE: int = 2

# Pagination
VIEW_COUNT: int = 20
NUM_ADJACENT :int = 2

# doctor/models.py
GENDER_CHOICE = (
    ('0', '남'),
    ('1', '여')
)

DANGER_LEVEL = (
    ('0', '정상'),
    ('1', '비정상'),
)

CLASS_NAME_DISEASES = ['amd', 'diabetic', 'glaucoma', 'erm', 'normal']
from core.constants import CLASS_NAME_DISEASES


class HistoryChecker:
    _SHORT_DESCRIPTIONS = {
        'check_left_image': "Left Image",
        'check_right_image': "Right Image",
        'check_left_image_heat': "Left Heat",
        'check_right_image_heat': "Right Heat",
        'check_disease_left': "Left Disease",
        'check_disease_right': "Right Disease",
        'check_memo': "Memo"
    }

    _HISTORY_CHILD = [
        '환자이름',
        '방문일자',
        '좌안',
        '우안',
        '좌안히트맵',
        '우안히트맵',
        '좌안병변',
        '우안병변',
        '메모'
    ]

    @classmethod
    def get_short_descriptions(cls):
        return cls._SHORT_DESCRIPTIONS

    @classmethod
    def get_history_child(cls):
        return cls._HISTORY_CHILD

    @classmethod
    def check_image(cls, image=None):
        if image:
            return "있음"
        return "없음"

    @classmethod
    def check_disease(cls, disease):
        if not disease:
            return "없음"
        if any(getattr(disease, val) is None for val in CLASS_NAME_DISEASES):
            return "없음"
        if sum(int(getattr(disease, val)) for val in CLASS_NAME_DISEASES) == 1:
            return "있음"
        return "없음"

    @classmethod
    def set_short_descriptions(cls, fields):
        for field in fields:
            setattr(field, 'short_description', cls.SHORT_DESCRIPTIONS[field])


class PermissionControlMixin:
    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


class NoChangePermissionMixin:
    def has_change_permission(self, request, obj=None):
        return False


class NoAddPermissionMixin:
    def has_add_permission(self, request, obj=None):
        return False


class NoDeletePermissionMixin:
    def has_delete_permission(self, request, obj=None):
        return False

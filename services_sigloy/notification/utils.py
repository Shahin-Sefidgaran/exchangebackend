from authentication.shared.classes import ThisUser


def get_id_key(user: ThisUser) -> str:
    """we use this function to identify user notifications by this column and change it easily
    whenever we want """
    return str(user.id)

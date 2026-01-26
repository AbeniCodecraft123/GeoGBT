from flask import jsonify
from main import Chats, current_user
def see_chats():
    chats = Chats.query.filter_by(user_id=current_user.id)\
                       .order_by(Chats.created_at.asc())\
                       .all()

    return jsonify([
        {
            "id": chat.id,
            "question": chat.question,
            "answer": chat.answer,
            "created_at": chat.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for chat in chats
    ])
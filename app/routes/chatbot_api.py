from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.llm_service import LLMService

chatbot_bp = Blueprint('chatbot', __name__)
llm = LLMService()

@chatbot_bp.route('/get-response', methods=['POST'])
@login_required
def get_response():
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({"reply": "No message received"}), 400

    # 1. Ask LLM to interpret command
    interpretation = llm.interpret_command(message)
    
    if "error" in interpretation:
        # If it's an error, it might just be conversational. Let's try chat mode.
        reply = llm.generate_chat_response(message)
        return jsonify({"reply": reply})

    # 2. Extract operation and entity from JSON
    operation = interpretation.get('operation')
    entity = interpretation.get('entity')
    params = interpretation.get('parameters', {})

    # 3. Handle database operations
    result = execute_db_action(operation, entity, params)
    
    # 4. If the DB action wasn't understood, just give a chat response
    if not result:
        reply = llm.generate_chat_response(message)
        return jsonify({"reply": reply})

    return jsonify({"reply": result})

def execute_db_action(op, entity, params):
    from app.models.guest import Guest
    from app.models.event import Event
    from app.models.rsvp import RSVP
    from app.extensions import db
    import datetime

    try:
        if entity == 'guest':
            if op == 'list':
                guests = Guest.query.filter_by(owner_id=current_user.id).all() if not current_user.is_admin else Guest.query.all()
                if not guests: return "You have no guests in your list."
                return "Your guests:\n" + "\n".join([f"- {g.name} ({g.email})" for g in guests])
            
            elif op == 'add':
                name = params.get('name')
                email = params.get('email')
                if not name or not email:
                    return "I need both a name and an email to add a guest."
                
                existing = Guest.query.filter_by(email=email, owner_id=current_user.id).first()
                if existing:
                    return f"Guest {name} with email {email} already exists."
                    
                guest = Guest(name=name, email=email, owner_id=current_user.id)
                db.session.add(guest)
                db.session.commit()
                return f"Successfully added guest {name}."

            elif op == 'delete':
                name = params.get('name')
                if not name: return "I need the guest's name to delete them."
                
                guest = Guest.query.filter(Guest.name.ilike(f"%{name}%"), Guest.owner_id == current_user.id).first()
                if not guest:
                    return f"Could not find a guest named {name}."
                
                db.session.delete(guest)
                db.session.commit()
                return f"Successfully removed guest {guest.name}."

        elif entity == 'event':
            if op == 'list':
                events = Event.query.filter_by(owner_id=current_user.id).all() if not current_user.is_admin else Event.query.all()
                if not events: return "You have no events scheduled."
                return "Your events:\n" + "\n".join([f"- {e.name} on {e.date.strftime('%b %d, %Y')}" for e in events])
            
            elif op == 'add':
                name = params.get('name')
                date_str = params.get('date')
                location = params.get('location', 'TBD')
                
                if not name or not date_str:
                    return "I need an event name and date to create it."
                
                try:
                    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                         date_obj = datetime.datetime.now()
                         
                event = Event(name=name, date=date_obj, location=location, owner_id=current_user.id)
                db.session.add(event)
                db.session.commit()
                return f"Successfully created event '{name}'."
                
            elif op == 'delete':
                name = params.get('name')
                if not name: return "I need the event name to delete it."
                
                event = Event.query.filter(Event.name.ilike(f"%{name}%"), Event.owner_id == current_user.id).first()
                if not event: return f"Could not find an event named {name}."
                
                db.session.delete(event)
                db.session.commit()
                return f"Successfully deleted event {event.name}."

        elif entity == 'rsvp':
            if op == 'record' or op == 'add':
                guest_name = params.get('guest') or params.get('guest_name')
                event_name = params.get('event') or params.get('event_name')
                status = params.get('status', 'attending').lower()
                
                if status in ['yes', 'confirm', 'confirmed']: status = 'attending'
                elif status in ['no', 'decline', 'declined', 'not attending']: status = 'not_attending'
                else: status = 'maybe'
                
                if not guest_name or not event_name:
                    return "I need both the guest's name and the event's name to record an RSVP."
                    
                guest = Guest.query.filter(Guest.name.ilike(f"%{guest_name}%"), Guest.owner_id == current_user.id).first()
                if not guest: return f"Could not find guest {guest_name}."
                
                event = Event.query.filter(Event.name.ilike(f"%{event_name}%"), Event.owner_id == current_user.id).first()
                if not event: return f"Could not find event {event_name}."
                
                existing_rsvp = RSVP.query.filter_by(guest_id=guest.id, event_id=event.id).first()
                if existing_rsvp:
                    existing_rsvp.status = status
                    db.session.commit()
                    return f"Updated RSVP for {guest.name} to {event.name} as {status}."
                else:
                    new_rsvp = RSVP(guest_id=guest.id, event_id=event.id, status=status)
                    db.session.add(new_rsvp)
                    db.session.commit()
                    return f"Recorded new RSVP for {guest.name} to {event.name} as {status}."
                    
    except Exception as e:
        db.session.rollback()
        return f"Database error occurred: {str(e)}"
        
    return None

@chatbot_bp.route('/analyze-sentiment', methods=['POST'])
@login_required
def analyze_sentiment():
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        result = llm.analyze_sentiment(text)
        if "error" in result:
            return jsonify(result), 503
        return jsonify({"analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


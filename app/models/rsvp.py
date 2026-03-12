from app.extensions import db

class RSVP(db.Model):
    __tablename__ = 'rsvps'

    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    # Status can be 'attending', 'not_attending', 'maybe'
    status = db.Column(db.String(20), nullable=False, default='maybe')
    plus_ones_count = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    guest = db.relationship('Guest', back_populates='rsvps')
    event = db.relationship('Event', back_populates='rsvps')

    # Ensure a guest can only RSVP once per event
    __table_args__ = (
        db.UniqueConstraint('guest_id', 'event_id', name='uq_rsvp_guest_event'),
    )

    def __repr__(self):
        return f'<RSVP {self.guest.name} -> {self.event.name}: {self.status}>'

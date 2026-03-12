from app.extensions import db

class Guest(db.Model):
    __tablename__ = 'guests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    dietary_needs = db.Column(db.String(200))
    plus_one_allowed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('User', back_populates='guests')
    
    # Relationships
    rsvps = db.relationship('RSVP', back_populates='guest', cascade='all, delete-orphan')

    # Ensure email is unique per user, but allow different users to have guests with same email
    __table_args__ = (
        db.UniqueConstraint('email', 'owner_id', name='uq_guest_email_owner'),
    )

    def __repr__(self):
        return f'<Guest {self.name}>'

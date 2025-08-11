from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Inventario(db.Model):
    __tablename__ = 'inventario'

    id          = db.Column(db.Integer,     autoincrement=True, index=True)  # Indexed Column
    ip          = db.Column(db.String(15),  primary_key=True)  # Primary Key
    tag         = db.Column(db.String(50),  nullable=False)
    marca       = db.Column(db.String(50),  nullable=False)
    rol         = db.Column(db.String(50),  nullable=False)
    tipo        = db.Column(db.String(50),  nullable=False)
    snmp_conf   = db.Column(db.Integer,     nullable=False)
    anotacion   = db.Column(db.String(50),  nullable=True)
    gps         = db.Column(db.Text,        nullable=True)

    def to_dict(self):
        return {
            "ip": self.ip,
            "id": self.id,
            "tag": self.tag,
            "marca": self.marca,
            "rol": self.rol,
            "tipo": self.tipo,
            "snmp_conf": self.snmp_conf,
            "anotacion": self.anotacion,
            "gps": self.gps,
        }
    

class Latencia(db.Model):
    __tablename__ = 'latencia'

    id          = db.Column(db.Integer,     primary_key=True,   autoincrement=True)  # Primary key
    ip          = db.Column(db.String(15),  index=True,         nullable=False)  # Indexed column
    latencia    = db.Column(db.Float,       nullable=False)  # Float column
    fecha       = db.Column(db.DateTime,    nullable=False)  # Datetime column
    fecha_DB    = db.Column(db.DateTime,    nullable=False,     server_default=db.func.current_timestamp())  # Default to current timestamp

    def __repr__(self):
            return f"<Latencia id={self.id} ip={self.ip} latencia={self.latencia} fecha={self.fecha} fecha_DB={self.fecha_DB}>"
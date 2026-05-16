from datetime import datetime, timezone
from extensions import db

class BiliVideoUser(db.Model):
    """B站视频-用户关联表（多对多关系）"""
    __tablename__ = 'bili_video_user'
    
    id = db.Column(db.Integer, primary_key=True)
    bvid = db.Column(db.String(20), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_watched_at = db.Column(db.DateTime, nullable=True)
    
    # 联合唯一约束：同一用户不能重复添加同一视频
    __table_args__ = (
        db.UniqueConstraint('bvid', 'user_id', name='unique_bili_video_user'),
    )
    
    user = db.relationship('User', backref=db.backref('bili_videos', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'bvid': self.bvid,
            'user_id': self.user_id,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'last_watched_at': self.last_watched_at.isoformat() if self.last_watched_at else None
        }

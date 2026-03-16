from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(100), unique=True, nullable=False)
    name = Column(String(200))
    location = Column(String(200))
    bio = Column(Text)
    company = Column(String(200))
    blog = Column(String(200))
    email = Column(String(200))
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    public_repos = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Relationship to repositories
    repositories = relationship("Repository", back_populates="owner")

    def __repr__(self):
        return f"<User(login='{self.login}', name='{self.name}')>"

class Repository(Base):
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(200), nullable=False)
    full_name = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    topics = Column(JSON)  # Store as a list of strings
    primary_language = Column(String(100))
    stargazers_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    watchers_count = Column(Integer, default=0)
    open_issues_count = Column(Integer, default=0)
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    pushed_at = Column(DateTime)
    
    license = Column(String(100))
    readme_content = Column(Text)
    
    # AI Classification
    industry_classification = Column(String(100))
    
    # Relationship to owner
    owner = relationship("User", back_populates="repositories")
    
    # Relationship to detailed languages
    languages = relationship("RepositoryLanguage", back_populates="repository")

    def __repr__(self):
        return f"<Repository(full_name='{self.full_name}', stars={self.stargazers_count})>"

class RepositoryLanguage(Base):
    __tablename__ = 'repository_languages'

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey('repositories.id'))
    language_name = Column(String(100), nullable=False)
    bytes_count = Column(Integer, nullable=False)
    
    # Relationship to repository
    repository = relationship("Repository", back_populates="languages")

    def __repr__(self):
        return f"<RepositoryLanguage(repo_id={self.repo_id}, lang='{self.language_name}', bytes={self.bytes_count})>"

"""
    This model represents a set of tests (I.E. Router and Phone) which belong to
    a user.

    Properties shared between multiple tests run by the same user should be 
    stored in this class.

    Author: Zach Anders
    Date: 02/08/2015
"""

from flask.ext.sqlalchemy import SQLAlchemy
from app import db
from datetime import datetime
from .test_result import TestResult

class TestSet(db.Model):
    __tablename__ = "TestSet"
    set_id = db.Column('set_id', db.Integer, primary_key=True)
    loc_latitude = db.Column('loc_latitude', db.Float)
    loc_longitude = db.Column('loc_longitude', db.Float)
    recorded = db.Column('recorded', db.DATETIME)
    owner_id = db.Column('owner_id', db.ForeignKey('User.user_id'))
    tests = db.relationship('TestResult', backref='parent_set')
    owner = db.relationship('User')

    @staticmethod
    def get_all_user_sets(owner):
        """ Retrieve all of the test sets that are associated with the user "owner" """
        return db.session.query(TestSet)\
            .filter(TestSet.owner_id == owner.user_id)\
            .order_by(TestSet.recorded.desc())\
            .all()

    @staticmethod
    def get_set_by_id(set_id):
        return db.session.query(TestSet).filter(
                TestSet.set_id == set_id
                ).first()

    def __init__(self, owner):
        """ Create a new test set, which belongs to the given user.
            By default, sets the recorded datetime to the current datetime."""
        self.owner_id = owner.user_id
        self.recorded = datetime.now()
        db.session.add(self)

    def new_result(self, device_type=None):
        """ Create and return a new TestResult inside the current test set. """
        res = TestResult(device_type=device_type)
        self.tests.append(res)

        return res

    def save(self):
        """ Save the record to the database. """
        db.session.commit()

    def delete(self):
        """ Deletes this test set and everything under it. """
        for test in self.tests:
            db.session.delete(test)
        db.session.delete(self)
        db.session.commit()

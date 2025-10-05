Add relation [Trasaction Status Example]

- Ensure field and foreign key for relationship is defined
    status_id = Column(Integer, ForeignKey("list_status_types.id"), nullable=False)

- Ensure relationship and field is defined
    status = relationship("StatusTypeDB", back_populates="postings", lazy='selectin')

- Ensure corresponding class has field populated
    transactions = relationship("TransactionDB", back_populates="status")

- Most important, ensure class for detail has the object defined
  
    class TransactionWithDetail(Transaction):
        status: StatusType
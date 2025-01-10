from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time

from database.connection import get_db
from models.machine import Machine
from schemas.machine import MachineBase, MachineResponse

router = APIRouter(prefix="/machines", tags=["machines"])

@router.post("/", response_model=MachineResponse)
def create_machine(machine: MachineBase, db: Session = Depends(get_db)):
    db_machine = Machine(
        **machine.dict(),
        created_at=int(time.time())
    )
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@router.get("/", response_model=List[MachineResponse])
def get_machines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    machines = db.query(Machine).offset(skip).limit(limit).all()
    return machines

@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(machine_id: int, machine: MachineBase, db: Session = Depends(get_db)):
    db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    for key, value in machine.dict().items():
        setattr(db_machine, key, value)
    
    db.commit()
    db.refresh(db_machine)
    return db_machine

@router.delete("/{machine_id}")
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    db.delete(db_machine)
    db.commit()
    return {"message": "Machine deleted successfully"}
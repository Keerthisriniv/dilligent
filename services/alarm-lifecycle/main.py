from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Literal
import time


class Alarm(BaseModel):
    id: str
    severity: Literal["info", "warning", "critical"]
    message: str
    status: Literal["open", "acknowledged", "resolved"] = "open"
    created_at: float = time.time()
    updated_at: float = time.time()


class AlarmAction(BaseModel):
    action: Literal["ack", "resolve"]
    note: str | None = None


app = FastAPI(title="Alarm Lifecycle API")
alarms: Dict[str, Alarm] = {}


@app.post("/alarms", response_model=Alarm)
def create_alarm(alarm: Alarm):
    if alarm.id in alarms:
        raise HTTPException(status_code=409, detail="Alarm already exists")
    now = time.time()
    alarm.created_at = now
    alarm.updated_at = now
    alarms[alarm.id] = alarm
    return alarm


@app.get("/alarms/{alarm_id}", response_model=Alarm)
def get_alarm(alarm_id: str):
    if alarm_id not in alarms:
        raise HTTPException(status_code=404, detail="Not found")
    return alarms[alarm_id]


@app.post("/alarms/{alarm_id}/action", response_model=Alarm)
def act_alarm(alarm_id: str, action: AlarmAction):
    if alarm_id not in alarms:
        raise HTTPException(status_code=404, detail="Not found")
    alarm = alarms[alarm_id]
    if action.action == "ack":
        alarm.status = "acknowledged"
    elif action.action == "resolve":
        alarm.status = "resolved"
    alarm.updated_at = time.time()
    alarms[alarm_id] = alarm
    return alarm



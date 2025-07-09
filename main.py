from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates 
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from datetime import datetime,timezone

app = FastAPI()
firestore_db = firestore.Client()
firebase_request_adapter = requests.Request()

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates (directory="templates")

@app.get("/", response_class=HTMLResponse) 
async def root(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token= None

    if id_token:
       try:
          user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
       except ValueError as err:
       
        
         print(str(err))

    return templates.TemplateResponse('main.html', {'request': request, 'user_token': user_token, 'error_message': error_message})


def add_room(room_number):
    try:
        room_ref = firestore_db.collection('rooms').document()
        room_data = {
            'number': room_number,
            'days': [] 
        }
        room_ref.set(room_data)
        return room_ref.id
    except Exception as e:
        print(f"Error adding room to Firestore: {e}")
        return None

def add_day(date):
    try:
        day_ref = firestore_db.collection('days').document()
        day_data = {
            'date': date,
            'bookings': [] 
        }
        day_ref.set(day_data)
        return day_ref.id
    except Exception as e:
        print(f"Error adding day to Firestore: {e}")
        return None
    
@app.get("/book_room", response_class=HTMLResponse)
async def book_room_form(request: Request):
    return templates.TemplateResponse("book_room.html", {"request": request})

@app.post("/book_room", response_class=HTMLResponse)
async def book_room_submit(request: Request):
    form = await request.form()

    room_number = form.get("room_number")
    start_date = form.get("start_date")
    checkin_time = form.get("checkin_time")
    end_date = form.get("end_date")
    checkout_time = form.get("checkout_time")
    
    id_token = request.cookies.get("token")
    user_id = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_id = user_token.get("user_id")
        except ValueError as err:
            print(str(err))

    
    
    booking_data = {
        "room_number": room_number,
        "start_date": start_date,
        "checkin_time":checkin_time,
        "end_date": end_date,
        "checkout_time":checkout_time,
        "user_id": user_id,
        
    }
    firestore_db.collection("bookings").add(booking_data)

   
    days_ref = firestore_db.collection("days")
    if not days_ref.document(start_date).get().exists:
        days_ref.document(start_date).set({})

    
    days_ref.document(start_date).update({
        f"bookings.{room_number}": {
            "start_date": start_date,
            "end_date": end_date,
            "user_id": user_id,
        
        }
    })

    return templates.TemplateResponse("book_room.html", {"request": request, "room_number": room_number, "start_date": start_date, "end_date": end_date, "user_id": user_id})

@app.get("/add_room", response_class=HTMLResponse)
async def add_room_form(request: Request):
    return templates.TemplateResponse("add_room.html", {"request": request})

@app.post("/add_room", response_class=HTMLResponse)
async def add_room_submit(request: Request):
    form = await request.form()

    room_number = form.get("room_number")
    user_id = None

    
    id_token = request.cookies.get("token")
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_id = user_token.get("user_id")
        except ValueError as err:
            print(str(err))

    if not user_id:
        return templates.TemplateResponse("add_room.html", {"request": request, "message": "User not authenticated"})

    try:
        existing_rooms = firestore_db.collection('rooms').where("room_number", "==", room_number).stream()
        if any(existing_rooms):
            return templates.TemplateResponse("add_room.html", {"request": request, "message": "A room with the same number already exists"})
    except Exception as e:
        print(f"Error checking existing rooms from Firestore: {e}")
        return templates.TemplateResponse("add_room.html", {"request": request, "message": "An error occurred while checking existing rooms. Please try again."})

    try:
        room_ref = firestore_db.collection('rooms').document()
        room_data = {
            'room_number': room_number,
            'user_id': user_id,  
        }
        room_ref.set(room_data)
        message = f"Room {room_number} added successfully!"
    except Exception as e:
        print(f"Error adding room to Firestore: {e}")
        message = "Failed to add room. Please try again."

    return templates.TemplateResponse("add_room.html", {"request": request, "message": message})

@app.get("/list_rooms", response_class=HTMLResponse)
async def list_rooms(request: Request):
    try:
        rooms_ref = firestore_db.collection('rooms').stream()
        rooms = [doc.to_dict() for doc in rooms_ref]

        room_names = []
        for booking_doc in firestore_db.collection("bookings").stream():
            room_names.append(booking_doc.get("room_number"))

    except Exception as e:
        print(f"Error fetching rooms from Firestore: {e}")
        rooms = []

    return templates.TemplateResponse("list_rooms.html", {"request": request, "rooms": rooms, "room_names": room_names})

@app.post("/list_rooms", response_class=HTMLResponse)
async def submit_list_rooms(request: Request, room_number: str = Form(...)):
    try:
        existing_rooms = firestore_db.collection('rooms').where("room_number", "==", room_number).stream()
        if any(existing_rooms):
            return "A room with the same name already exists"
    except Exception as e:
        print(f"Error checking existing rooms from Firestore: {e}")
        return "An error occurred while checking existing rooms. Please try again."

    if not room_number or len(room_number.strip()) == 0:
        return "Room nunmber cannot be empty"
    

    try:
        room_ref = firestore_db.collection('rooms').document()
        room_data = {
            'room_number': room_number,
            'bookings': [] 
        }
        room_ref.set(room_data)
        message = f"Room {room_number} added successfully!"
    except Exception as e:
        print(f"Error adding room to Firestore: {e}")
        return "Failed to add room. Please try again."


    return templates.TemplateResponse("list_rooms.html", {"request": request, "message": message})

@app.post("/delete_room", response_class=RedirectResponse)
async def delete_room(request: Request, room_number: str = Form(...)):
    try:
        room_ref = firestore_db.collection("rooms").where("room_number", "==", room_number).stream()
        room_doc = next(room_ref, None)
        if room_doc:
            firestore_db.collection("rooms").document(room_doc.id).delete()
            return RedirectResponse('/list_rooms', status_code=302)
        else:
            return "Room not found", 404
    except Exception as e:
        print(f"Error deleting room: {e}")
        return "An error occurred while deleting the room"


@app.get("/user_bookings", response_class=HTMLResponse)
async def user_bookings(request: Request):

    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None
    user_bookings = []

    
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_id = user_token.get("user_id") if user_token else None
            if user_id:
                
                firestore_db = firestore.Client()
                query = firestore_db.collection("bookings").where("user_id", "==", user_id).stream()
                user_bookings = [doc.to_dict() for doc in query]
        except ValueError as err:
            error_message = str(err)
        except Exception as e:
            error_message = f"Error retrieving user bookings: {e}"

    return templates.TemplateResponse('user_bookings.html', {'request': request, 'user_token': user_token, 'error_message': error_message, 'user_bookings': user_bookings, 'user_id': user_id})

@app.post("/delete_booking", response_class=RedirectResponse)
async def delete_booking(request: Request):
    form = await request.form()
    room_number = form.get('room_number')
    start_date = form.get('start_date')

    try:
        query = firestore_db.collection("bookings").where("room_number", "==", room_number).where("start_date", "==", start_date).stream()
        for doc in query:
            doc.reference.delete()
        return RedirectResponse('/', status_code=302)
    except Exception as e:
        print(f"Error deleting booking: {e}")
        return RedirectResponse('/', status_code=302)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
@app.get("/search_room", response_class=HTMLResponse)
async def search_room_form(request: Request):
   
    return templates.TemplateResponse("search_room.html", {"request": request})

@app.post("/search_room", response_class=HTMLResponse)
async def search_room_submit(request: Request):
    
    form = await request.form()
    room_number = form.get("room_number")

    
    id_token = request.cookies.get("token")
    user_id = None
    user_bookings = []

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_id = user_token.get("user_id")
            if user_id:
                query = firestore_db.collection("bookings").where("user_id", "==", user_id).where("room_number", "==", room_number).stream()
                user_bookings = [doc.to_dict() for doc in query]
        except ValueError as err:
            print(str(err))  
        except Exception as e:
            print(f"Error retrieving user bookings: {e}")

    return templates.TemplateResponse("search_result.html", {"request": request, "user_bookings": user_bookings, "room_number": room_number})


@app.get("/edit_booking", response_class=HTMLResponse)
async def edit_booking_form(request: Request, room_number: str, start_date: str):
    try:
        query = firestore_db.collection("bookings").where("room_number", "==", room_number).where("start_date", "==", start_date).stream()
        booking_data = [doc.to_dict() for doc in query]
        if booking_data:
            return templates.TemplateResponse("edit_booking.html", {"request": request, "booking_data": booking_data[0]})
        else:
            return "Booking not found"
    except Exception as e:
        print(f"Error retrieving booking data: {e}")
        return "An error occurred while retrieving booking data"
    
@app.post("/update_booking", response_class=RedirectResponse)
async def update_booking(request: Request):
    form = await request.form()
    room_number = form.get('room_number')
    start_date = form.get('start_date')
    checkin_time = form.get("checkin_time")
    end_date = form.get("end_date")
    checkout_time = form.get("checkout_time")

    try:

        query = firestore_db.collection("bookings").where("room_number", "==", room_number).stream()
        for doc in query:
           
            doc.reference.update({
                "start_date": start_date,
                "end_date": end_date,
                "checkin_time": checkin_time,
                "checkout_time": checkout_time
                })
        return RedirectResponse('/user_bookings', status_code=302)
    except Exception as e:
        print(f"Error updating booking: {e}")
        return RedirectResponse('/user_bookings', status_code=302)

@app.get("/bookings_for_day", response_class=HTMLResponse)
async def bookings_for_day_form(request: Request):
    return templates.TemplateResponse("bookings_for_day.html", {"request": request})
 
@app.post("/filter-by-date", response_class=HTMLResponse)
async def filter_by_date(request: Request, selected_date: str = Form(...)):
    try:
       
        selected_datetime = datetime.strptime(selected_date, "%Y-%m-%d")
        
        bookings_ref = firestore_db.collection("bookings").where("start_date", "==", selected_date).stream()
        filtered_bookings = [doc.to_dict() for doc in bookings_ref]
        
        return templates.TemplateResponse("bookings_for_day.html", {"request": request, "bookings": filtered_bookings})
    except Exception as e:
        error_message = f"Error: {e}"
        return templates.TemplateResponse("bookings_for_day.html", {"request": request, "error_message": error_message})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


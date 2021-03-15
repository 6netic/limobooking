import os
import dotenv
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.http import Http404
from .viewsCompute import *
from .models import Booking
from .forms import ReservationForm
from .forms import SearchForm


dotenv.load_dotenv(os.path.join('.env'))


def index(request):
    """ Index of the application, first access to the app """

    return render(request, "booking/index.html")


def home(request):
    """ Homepage of the application """

    return render(request, "booking/home.html")


def aeroports(request):
    """ Homepage of the application """

    return render(request, "booking/aeroports.html")


def gares(request):
    """ Homepage of the application """

    return render(request, "booking/gares.html")


def otherDestination(request):
    """ Homepage of the application """

    googleApiKey = os.getenv("GOOGLE_API_KEY")
    if request.method == 'GET':
        # destination is sent via GET method
        if (request.GET.get("destination")):
            destination = request.GET.get("destination")
            return redirect('booking:displayJourney', destination=destination)
        # This is the first access to autreDestination page
        else:
            form = ReservationForm()
            return render(request, "booking/autredestination.html", locals())


def displayJourney(request, destination):
    """ View for displaying empty form in destinations.html page """

    googleApiKey = os.getenv("GOOGLE_API_KEY")
    # This is the first time we access the page with destination value given
    if request.method == 'GET':
        form = ReservationForm()
        return render(request, "booking/destinations.html", locals())


def selectJourney(request):
    """ Selecting required date and time """

    googleApiKey = os.getenv("GOOGLE_API_KEY")
    # Form is sent with POST method
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            # Retrieving datas from form
            destination = form.cleaned_data['destination']
            departureDate = form.cleaned_data['departureDate']
            hour = form.cleaned_data['hour']
            minute = form.cleaned_data['minute']
            sharing = form.cleaned_data['sharing']
            departureTime = hour + ":" + minute
            firstname = form.cleaned_data['firstname']
            lastname = form.cleaned_data['lastname']
            email = form.cleaned_data['email']

            dayOfReservation = departureDate.strftime("%a")
            if (dayOfReservation == "Mon" or dayOfReservation == "Tue" or
                dayOfReservation == "Wed" or dayOfReservation == "Thu" or
                    dayOfReservation == "Fri"):
                if (int(hour) >= 8 and int(hour) < 20):
                    tarifKilometre = 1.01
                else:
                    tarifKilometre = 1.56
            if (dayOfReservation == "Sat" or dayOfReservation == "Sun" or
               (departureDate in bankHolidayDates)):
                tarifKilometre = 1.61

            distance = float(request.POST.get("distance")) / 1000
            prixCourse = (tarifKilometre * distance)
            prixCourse = round(prixCourse, 2)
            # Looking for other bookings
            try:
                bookingsInBase = Booking.objects.filter(
                    departureDate__exact=departureDate).filter(
                    sharing__exact=sharing).filter(
                    destination__exact=destination
                )
                if bookingsInBase:
                    bookingList = []
                    pricesDict = {}
                    for booking in bookingsInBase:
                        bookingList.append(booking.departureTime)
                    uniqueBookingList = set(bookingList)
                    for b in uniqueBookingList:
                        if (bookingList.count(b) + 1) <= 3:
                            reductRate = 0.95
                        elif (bookingList.count(b) + 1) > 3 and (bookingList.count(b) + 1) <= 7:
                            reductRate = 0.92
                        elif (bookingList.count(b) + 1) > 7 and (bookingList.count(b) + 1) <= 22:
                            reductRate = 0.84
                        elif (bookingList.count(b) + 1) > 22 and (bookingList.count(b) + 1) <= 54:
                            reductRate = 0.76
                        pricesDict[b] = round(prixCourse * reductRate, 2)
                else:
                    onlyOne = True
            except:
                pass
                # On pourrait faire un retour HTTP 404

            return render(request, "booking/destinations.html", locals())


def recordJourney(request):
    """ Records values in the database """

    if request.method == 'POST':

        # Retrieve first group of variables
        destination = request.POST.get("destination")
        dep = (request.POST.get("departureDate")).split("-")
        departureDate = date(int(dep[2]), int(dep[1]), int(dep[0]))
        departureTime = request.POST.get("departureTime")
        sharing = request.POST.get("sharing")
        lastname = request.POST.get("lastname")
        firstname = request.POST.get("firstname")
        email = request.POST.get("email")
        prixCourse = float(request.POST.get("prixCourse"))
        # Register booking into database
        if request.POST.get("validation"):
            try:
                newBooking = Booking.objects.create(
                    destination=destination,
                    departureDate=departureDate,
                    departureTime=departureTime,
                    sharing=sharing,
                    lastname=lastname,
                    firstname=firstname,
                    email=email,
                    price=prixCourse,
                )
                messageOk = "Réservation enregistrée"
                message = True
                # return render(request, "booking/record.html", locals())
            except:
                messageNok = "Vous avez déjà effectué une réservation à cette date pour cette destination"
                message = True
            return render(request, "booking/record.html", locals())

        return render(request, "booking/record.html", locals())


def cancelJourney(request):
    """ Cancels a booking from the database """

    if request.method == 'GET':
        if request.GET.get("email"):
            email = request.GET.get("email")
            departureDate = request.GET.get("departureDate")
            try:
                cancel = Booking.objects.filter(email__contains=email)\
                                .filter(departureDate=departureDate)
                if cancel:
                    return render(request, "booking/cancel.html", locals())
                else:
                    message = "Aucune réservation trouvée à cette date"
                    return render(request, "booking/cancel.html", locals())
            except:
                pass

        first = True
        form = SearchForm()
        return render(request, "booking/cancel.html", locals())

    if request.method == 'POST':
        id = request.POST.get("id")
        try:
            delete = Booking.objects.filter(pk=id).delete()
            messDel = "La réservation a bien été annulée."
        except:
            pass

        return render(request, "booking/cancel.html", locals())


/* =========================
   BOOKING SYSTEM
========================= */

const bookingForm = document.getElementById("bookingForm");
const bookingMessage = document.getElementById("bookingMessage");

bookingForm.addEventListener("submit", async function(event) {

    event.preventDefault();

    const bookingData = {

        name: document.getElementById("name").value,

        phone: document.getElementById("phone").value,

        email: document.getElementById("email").value,

        vehicle: document.getElementById("vehicle").value,

        service: document.getElementById("service").value,

        date: document.getElementById("date").value,

        message: document.getElementById("message").value

    };


    bookingMessage.className = "booking-message";

    bookingMessage.textContent = "Submitting your booking...";

    bookingMessage.style.display = "block";


    try {

        const response = await fetch(
            "http://127.0.0.1:5000/booking",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(bookingData)
            }
        );


        const result = await response.json();


        if (response.ok) {

            bookingMessage.className =
                "booking-message success";

            bookingMessage.textContent =
                "✓ Booking received successfully! We will contact you shortly.";

            bookingForm.reset();

        } else {

            bookingMessage.className =
                "booking-message error";

            bookingMessage.textContent =
                result.error ||
                "Something went wrong. Please try again.";

        }

    } catch (error) {

        console.error(error);

        bookingMessage.className =
            "booking-message error";

        bookingMessage.textContent =
            "Unable to connect to the booking system. Please try again.";

    }

});


/* =========================
   SMOOTH NAVIGATION
========================= */

document.querySelectorAll('a[href^="#"]').forEach(function(link) {

    link.addEventListener("click", function(event) {

        event.preventDefault();

        const target =
            document.querySelector(this.getAttribute("href"));

        if (target) {

            target.scrollIntoView({
                behavior: "smooth"
            });

        }

    });

});


/* =========================
   MOBILE MENU
========================= */

const menuToggle =
    document.getElementById("menuToggle");

const navLinks =
    document.getElementById("navLinks");


menuToggle.addEventListener("click", function() {

    navLinks.classList.toggle("active");

});


/* Close mobile menu after clicking a link */

document.querySelectorAll(".nav-links a").forEach(function(link) {

    link.addEventListener("click", function() {

        navLinks.classList.remove("active");

    });

});
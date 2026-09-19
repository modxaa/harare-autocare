/* =========================
   MOBILE MENU
========================= */

const menuToggle = document.getElementById("menuToggle");
const navLinks = document.getElementById("navLinks");

if (menuToggle && navLinks) {

    menuToggle.addEventListener("click", function () {

        navLinks.classList.toggle("active");

    });

}


/* =========================
   CLOSE MOBILE MENU
========================= */

document.querySelectorAll(".nav-links a").forEach(function (link) {

    link.addEventListener("click", function () {

        if (navLinks) {
            navLinks.classList.remove("active");
        }

    });

});


/* =========================
   SMOOTH NAVIGATION
========================= */

document.querySelectorAll('a[href^="#"]').forEach(function (link) {

    link.addEventListener("click", function (event) {

        event.preventDefault();

        const target = document.querySelector(
            this.getAttribute("href")
        );

        if (target) {

            target.scrollIntoView({
                behavior: "smooth"
            });

        }

    });

});


/* =========================
   BOOKING FORM
========================= */

const bookingForm = document.getElementById("bookingForm");
const bookingMessage = document.getElementById("bookingMessage");

if (bookingForm) {

    bookingForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const formData = new FormData(bookingForm);

        const bookingData = {

            name: formData.get("name"),
            phone: formData.get("phone"),
            email: formData.get("email"),
            vehicle: formData.get("vehicle"),
            service: formData.get("service"),
            date: formData.get("date"),
            message: formData.get("message")

        };


        if (bookingMessage) {

            bookingMessage.textContent =
                "Submitting your booking...";

        }


        try {

            const response = await fetch("/booking", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(bookingData)

            });


            const result = await response.json();


            if (result.success) {

                bookingMessage.textContent =
                    "Booking submitted successfully!";

                bookingForm.reset();

            } else {

                bookingMessage.textContent =
                    result.message || "Something went wrong.";

            }


        } catch (error) {

            console.error(error);

            bookingMessage.textContent =
                "Unable to submit booking. Please try again.";

        }

    });

}
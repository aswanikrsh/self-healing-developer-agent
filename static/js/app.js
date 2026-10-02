/*
============================================================
SELF-HEALING DEVELOPER AGENT
PHASE 9 DASHBOARD JAVASCRIPT
============================================================
*/

document.addEventListener("DOMContentLoaded", function () {

    /*
    --------------------------------------------------------
    Prevent accidental double submission
    --------------------------------------------------------
    */

    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener("submit", function () {

            const submitButtons =
                form.querySelectorAll(
                    "button[type='submit'], input[type='submit']"
                );

            submitButtons.forEach(function (button) {

                if (button.dataset.submitted === "true") {
                    return;
                }

                button.dataset.submitted = "true";

                button.disabled = true;

            });

        });

    });


    /*
    --------------------------------------------------------
    Auto-hide messages
    --------------------------------------------------------
    */

    const messages =
        document.querySelectorAll(".message");

    messages.forEach(function (message) {

        setTimeout(function () {

            message.style.transition =
                "opacity 0.4s ease";

            message.style.opacity = "0";

            setTimeout(function () {

                message.remove();

            }, 400);

        }, 5000);

    });


    /*
    --------------------------------------------------------
    Confirm dangerous actions
    --------------------------------------------------------
    */

    const dangerousButtons =
        document.querySelectorAll(
            "[data-confirm]"
        );

    dangerousButtons.forEach(function (button) {

        button.addEventListener("click", function (event) {

            const message =
                button.dataset.confirm;

            if (
                message &&
                !window.confirm(message)
            ) {
                event.preventDefault();
            }

        });

    });

});
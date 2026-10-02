/* =========================================================
   Self-Healing Developer Agent
   Main JavaScript
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    console.log("Self-Healing Developer Agent loaded.");

    /* =====================================================
       Confirmation for approval buttons
       ===================================================== */

    const approvalButtons = document.querySelectorAll(
        ".approve-fix"
    );

    approvalButtons.forEach(function (button) {

        button.addEventListener("click", function (event) {

            const confirmed = confirm(
                "Are you sure you want to approve this AI-generated fix?"
            );

            if (!confirmed) {
                event.preventDefault();
            }

        });

    });


    /* =====================================================
       Confirmation for reject buttons
       ===================================================== */

    const rejectButtons = document.querySelectorAll(
        ".reject-fix"
    );

    rejectButtons.forEach(function (button) {

        button.addEventListener("click", function (event) {

            const confirmed = confirm(
                "Are you sure you want to reject this fix?"
            );

            if (!confirmed) {
                event.preventDefault();
            }

        });

    });


    /* =====================================================
       Show loading message when analyzing
       ===================================================== */

    const debugForms = document.querySelectorAll(
        ".debug-form"
    );

    debugForms.forEach(function (form) {

        form.addEventListener("submit", function () {

            const loading = document.querySelector(".loading");

            if (loading) {
                loading.style.display = "block";
            }

        });

    });


    /* =====================================================
       Copy code button
       ===================================================== */

    const copyButtons = document.querySelectorAll(
        ".copy-code"
    );

    copyButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            const targetId = button.dataset.target;
            const codeElement = document.getElementById(targetId);

            if (!codeElement) {
                return;
            }

            navigator.clipboard.writeText(
                codeElement.innerText
            ).then(function () {

                const originalText = button.innerText;

                button.innerText = "Copied!";

                setTimeout(function () {
                    button.innerText = originalText;
                }, 1500);

            });

        });

    });


    /* =====================================================
       Auto-hide alerts
       ===================================================== */

    const alerts = document.querySelectorAll(
        ".alert-auto-hide"
    );

    alerts.forEach(function (alert) {

        setTimeout(function () {

            alert.style.opacity = "0";

            setTimeout(function () {
                alert.remove();
            }, 500);

        }, 5000);

    });

});
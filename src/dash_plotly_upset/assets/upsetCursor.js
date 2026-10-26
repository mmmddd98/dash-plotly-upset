(function () {
    "use strict";

    function hasClickableCustomData(eventData) {
        if (!eventData || !eventData.points || eventData.points.length === 0) {
            return false;
        }

        const point = eventData.points[0];
        const cd = point.customdata;

        if (!cd || cd.length < 3) {
            return false;
        }

        const kind = String(cd[0]);
        return kind === "intersection" || kind === "set";
    }

    function attachCursorHandler() {
        const wrapper = document.getElementById("upset-plot");

        if (!wrapper) {
            return;
        }

        const plot = wrapper.querySelector(".js-plotly-plot");

        if (!plot || plot.__upsetCursorAttached) {
            return;
        }

        plot.__upsetCursorAttached = true;

        plot.on("plotly_hover", function (eventData) {
            if (hasClickableCustomData(eventData)) {
                wrapper.classList.add("upset-clickable-hover");
            } else {
                wrapper.classList.remove("upset-clickable-hover");
            }
        });

        plot.on("plotly_unhover", function () {
            wrapper.classList.remove("upset-clickable-hover");
        });
    }

    function startObserver() {
        attachCursorHandler();

        const observer = new MutationObserver(function () {
            attachCursorHandler();
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", startObserver);
    } else {
        startObserver();
    }
})();

(function () {
    var el = document.getElementById("clock");
    if (!el) return;
    function tick() {
        var d = new Date();
        el.textContent = d.toLocaleTimeString("en-GB", { hour12: false });
    }
    tick();
    setInterval(tick, 1000);
})();

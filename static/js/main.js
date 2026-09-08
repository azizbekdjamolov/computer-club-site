document.addEventListener('DOMContentLoaded', function () {
    // ---------- Lucide icons (initial render) ----------
    renderIcons();

    // ---------- Sidebar toggle ----------
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });
        document.addEventListener('click', function (e) {
            if (window.innerWidth <= 900 && sidebar.classList.contains('open')) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }

    // ---------- Notifications dropdown ----------
    const notifWrap = document.getElementById('notificationsWrap');
    const notifToggle = document.getElementById('notifToggle');
    const notifDropdown = document.getElementById('notifDropdown');
    if (notifWrap && notifToggle && notifDropdown) {
        notifToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            notifDropdown.classList.toggle('open');
        });
        document.addEventListener('click', function (e) {
            if (!notifWrap.contains(e.target)) notifDropdown.classList.remove('open');
        });
    }

    // ---------- Modals ----------
    const quickStartBtn = document.getElementById('quickStartBtn');
    const quickModal = document.getElementById('quickModal');

    window.openModal = function (id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.add('open');
        renderIcons();
    };
    window.closeModal = function () {
        document.querySelectorAll('.modal-backdrop').forEach(function (m) { m.classList.remove('open'); });
    };
    if (quickStartBtn && quickModal) {
        quickStartBtn.addEventListener('click', function () { openModal('quickModal'); });
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeModal();
    });
    document.querySelectorAll('.modal-backdrop').forEach(function (m) {
        m.addEventListener('mousedown', function (e) {
            if (e.target === m) m.classList.remove('open');
        });
    });

    // ---------- Dynamic computers for quick form ----------
    const qsRoom = document.getElementById('qsRoom');
    const qsComputer = document.getElementById('qsComputer');
    if (qsRoom && qsComputer) {
        qsRoom.addEventListener('change', function () {
            const rid = this.value;
            qsComputer.innerHTML = '<option value="">Yuklanmoqda...</option>';
            if (!rid) { qsComputer.innerHTML = '<option value="">-- Avval xonani tanlang --</option>'; return; }
            fetch('/rooms/' + rid + '/computers/')
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    qsComputer.innerHTML = '<option value="">-- Kompyuter --</option>';
                    data.computers.forEach(function (pc) {
                        const label = pc.status === 'reserved' ? ' (rezerv)' : pc.status === 'maintenance' ? ' (nosoz)' : pc.status === 'occupied' ? ' (band)' : '';
                        const o = document.createElement('option');
                        o.value = pc.id;
                        o.textContent = pc.name + label;
                        qsComputer.appendChild(o);
                    });
                })
                .catch(function () { qsComputer.innerHTML = '<option value="">Xatolik</option>'; });
        });
    }

    // ---------- Prefill start time in quick modal ----------
    const qsStart = document.getElementById('qsStart');
    if (qsStart && !qsStart.value) {
        qsStart.value = prefillNow();
    }

    // ---------- Auto-fill duration -> end time (and vice versa) ----------
    const duration = document.getElementById('qsDuration');
    const qsEnd = document.getElementById('qsEnd');
    if (duration && qsEnd && qsStart) {
        function addMinutes(iso, mins) {
            const d = new Date(iso);
            d.setMinutes(d.getMinutes() + mins);
            return toLocal(d);
        }
        duration.addEventListener('change', function () {
            if (this.value && qsStart.value) qsEnd.value = addMinutes(qsStart.value, parseInt(this.value));
        });
        qsEnd.addEventListener('change', function () {
            if (this.value && qsStart.value) {
                const ms = new Date(this.value) - new Date(qsStart.value);
                if (ms > 0) duration.value = Math.round(ms / 60000);
            }
        });
    }

    // ---------- Payment method grid (cash/card/...) ----------
    document.querySelectorAll('.pm-grid').forEach(function (grid) {
        const hidden = grid.dataset.target || 'payment_method';
        grid.querySelectorAll('button').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                grid.querySelectorAll('button').forEach(function (b) { b.classList.remove('selected'); });
                btn.classList.add('selected');
                const input = document.getElementById(hidden) || document.querySelector('input[name="' + hidden + '"]');
                if (input) input.value = btn.dataset.value;
            });
        });
    });

    // ---------- PC card click -> info modal ----------
    const pcModal = document.getElementById('pcModal');
    const pcModalBody = document.getElementById('pcModalBody');
    const statusText = { available: "Bo'sh", occupied: 'Band', reserved: 'Rezerv', maintenance: 'Nosoz' };

    document.querySelectorAll('.pc-card').forEach(function (card) {
        card.addEventListener('click', function (e) {
            e.preventDefault();
            const id = card.dataset.id;
            const name = card.dataset.name;
            const status = card.dataset.status;
            const roomId = card.dataset.room;
            const sessionId = card.dataset.session;

            if (status === 'occupied') {
                // Active session -> open dedicated detail modal (server-rendered)
                const sessModal = document.getElementById('sessModal' + sessionId);
                if (sessModal) { openModal('sessModal' + sessionId); return; }
                window.location.href = '/sessions/active/';
                return;
            }

            const timeInput = '<input type="datetime-local" name="start_time" id="pcStart" class="form-control" value="' + prefillNow() + '">';
            pcModalBody.innerHTML =
                '<div class="modal-head"><div><h3><i data-lucide="monitor"></i> ' + name + '</h3>' +
                '<div class="m-head-sub"><span class="status-pill ' + status + '">' + (statusText[status] || status) + '</span></div></div>' +
                '<button type="button" class="modal-close" onclick="closeModal()"><i data-lucide="x"></i></button></div>' +
                '<form method="post" action="' + window.QUICK_URL + '" id="pcStartForm">' +
                '<input type="hidden" name="csrfmiddlewaretoken" value="' + window.CSRF + '">' +
                '<input type="hidden" name="room" value="' + roomId + '">' +
                '<input type="hidden" name="computer" value="' + id + '">' +
                '<div class="form-group"><label>Mijoz ismi</label>' +
                '<input type="text" name="customer_name" class="form-control" required placeholder="Ali Valiyev"></div>' +
                '<div class="form-group"><label>Telefon</label>' +
                '<input type="text" name="phone" class="form-control" placeholder="998901234567"></div>' +
                '<div class="form-row"><div class="form-group"><label>Boshlash</label>' + timeInput + '</div>' +
                '<div class="form-group"><label>Muddat (daq)</label>' +
                '<input type="number" name="duration_minutes" class="form-control" min="1"></div></div>' +
                '<div class="form-row"><div class="form-group"><label>Tugash vaqti</label>' +
                '<input type="datetime-local" name="planned_end_time" class="form-control"></div>' +
                '<div class="form-group"><label>To\'lov</label>' +
                '<input type="number" name="paid_amount" class="form-control" min="0"></div></div>' +
                '<button type="submit" class="btn btn-primary btn-block btn-lg"><i data-lucide="play"></i> Sessiyani boshlash</button>' +
                '</form>';
            openModal('pcModal');
        });
    });

    // ---------- Global confirm on data-confirm forms ----------
    document.querySelectorAll('form[data-confirm]').forEach(function (f) {
        f.addEventListener('submit', function (e) {
            const msg = f.getAttribute('data-confirm');
            if (msg && !window.confirm(msg)) e.preventDefault();
        });
    });

    // ---------- Auto refresh ----------
    if (window.AUTO_REFRESH && AUTO_REFRESH > 0) {
        setInterval(function () {
            const searchInput = document.querySelector('.global-search input');
            if (searchInput && document.activeElement === searchInput) return;
            const path = window.location.pathname;
            if (path === '/' || path === '/sessions/active/') {
                location.reload();
            }
        }, AUTO_REFRESH * 1000);
    }
});

// ---------- Helpers ----------
function prefillNow() {
    const now = new Date();
    return toLocal(now);
}

function toLocal(d) {
    const pad = function (n) { return String(n).padStart(2, '0'); };
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
        'T' + pad(d.getHours()) + ':' + pad(d.getMinutes());
}

function fmtMoney(n) {
    return new Intl.NumberFormat('ru-RU').format(Math.round(n || 0)) + ' ' + (window.CURRENCY || 'UZS');
}
window.prefillNow = prefillNow;
window.fmtMoney = fmtMoney;

function renderIcons() {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
    }
}
window.renderIcons = renderIcons;
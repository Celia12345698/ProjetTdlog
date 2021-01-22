document.addEventListener('DOMContentLoaded', () => {

    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    const firstname = document.querySelector('#get-firstname').innerHTML;

    let room = "Fun"
    joinRoom("Fun");

    document.querySelector('#send_message').onclick = () => {
        socket.emit('incoming-msg', {'msg': document.querySelector('#user_message').value,
            'firstname': firstname, 'room': room});

        document.querySelector('#user_message').value = '';
    };

    socket.on('message', data => {

        if (data.msg) {
            const p = document.createElement('p');
            const span_firstname = document.createElement('span');
            const span_timestamp = document.createElement('span');
            const br = document.createElement('br')
            if (data.firstname == firstname) {
                    p.setAttribute("class", "my-msg");

                    span_firstname.setAttribute("class", "my-firstname");
                    span_firstname.innerText = data.firstname;

                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = data.time_stamp;

                    p.innerHTML += span_firstname.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML

                    document.querySelector('#display-message-section').append(p);
            }
            else if (typeof data.firstname !== 'undefined') {
                p.setAttribute("class", "others-msg");

                span_firstname.setAttribute("class", "other-firstname");
                span_firstname.innerText = data.firstname;

                span_timestamp.setAttribute("class", "timestamp");
                span_timestamp.innerText = data.time_stamp;

                p.innerHTML += span_firstname.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML;

                document.querySelector('#display-message-section').append(p);
            }
            else {
                printSysMsg(data.msg);
            }


        }
        scrollDownChatWindow();
    });

    document.querySelectorAll('.select-room').forEach(p => {
        p.onclick = () => {
            let newRoom = p.innerHTML
            if (newRoom === room) {
                msg = `Vous êtes déjà dans la salle ${room}.`;
                printSysMsg(msg);
            } else {
                leaveRoom(room);
                joinRoom(newRoom);
                room = newRoom;
            }
        };
    });

    document.querySelector("#logout-btn").onclick = () => {
        leaveRoom(room);
    };

    function leaveRoom(room) {
        socket.emit('leave', {'firstname': firstname, 'room': room});

        document.querySelectorAll('.select-room').forEach(p => {
            p.style.color = "black";
        });
    }

    function joinRoom(room) {

        socket.emit('join', {'firstname': firstname, 'room': room});

        document.querySelector('#' + CSS.escape(room)).style.color = "rgba(232,143,124)";

        document.querySelector('#display-message-section').innerHTML = '';

        document.querySelector("#user_message").focus();
    }

    function scrollDownChatWindow() {
        const chatWindow = document.querySelector("#display-message-section");
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function printSysMsg(msg) {
        const p = document.createElement('p');
        p.setAttribute("class", "system-msg");
        p.innerHTML = msg;
        document.querySelector('#display-message-section').append(p);
        scrollDownChatWindow()

        document.querySelector("#user_message").focus();
    }
});

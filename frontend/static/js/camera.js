// Set constraints for the video stream
var constraints = { video: { facingMode: "user" }, audio: false };
var track = null;
var user_id = 0;
var user_list = [];
var qr_url_dict = {};
var sharable_movie_link = null;

// Define constants
const cameraView = document.querySelector("#camera--view"),
    // cameraOutput = document.querySelector("#camera--output"),
    cameraSensor = document.querySelector("#camera--sensor"),
    cameraTrigger = document.querySelector("#camera--trigger"),
    qrcode = document.querySelector('.qrcode');

// Access the device camera and stream to cameraView
function cameraStart() {
    navigator.mediaDevices
        .getUserMedia(constraints)
        .then(function(stream) {
            track = stream.getTracks()[0];
            cameraView.srcObject = stream;
        })
        .catch(function(error) {
            console.error("Oops. Something is broken.", error);
        });
}

// function toggleCamera() {
//     alert('toggle');
//     // if ($("#camera-toggle").is(":checked")) {
//     //     cameraStart();
//     // } else {
//     //     track.stop();
//     // }
// }

$(function() {
    $('#camera-toggle').change(function() {
        if ($("#camera-toggle").is(":checked")) {
            cameraStart();
        } else {
            track.stop();
        } 
    })
});


setInterval(function() {
    for (let i = 0; i < user_list.length; i++) {
        ts = user_list[i];
        $.get("/server", {movie_id: ts}).done(function(data) {
            movie_link = JSON.parse(data).src;
            alert(data);
            sharable_movie_link = JSON.parse(data).sharable;
            // alert(movie_link); 
            if (movie_link != "") {
                $('#camera--output-user'.concat((user_id-1) % 3)).attr("visibility", "hidden");
                $('#video-user'.concat((user_id-1) % 3)).attr("visibility", "visible")
                $('#video-user'.concat((user_id-1) % 3)).attr("src", movie_link);
                user_list.splice(user_list.indexOf(ts), 1); 
                // $('#video-user'.concat(uid % 3)).get(0).load();
                // $('#video-user'.concat(uid % 3)).play();
                // $("#video-user".concat(user_list % 3).concat(' video source')).attr("visibility", "visible");
                // $("#video-user".concat(user_list % 3).concat(' video source')).attr("src", movie_link);
                // $("#video-user".concat(user_list % 3).concat(' video source')).load();
            } 
        });
    }
}, 5000);

$('a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
    pill_name = $(e.target).attr("id");
    pill_id = pill_name.charAt(pill_name.length-1);
    $('.qrcode').attr("src", qr_url_dict[parseInt(pill_id)]);
  });


// function requestQRCode(text_data){
//     var data = new FormData();
//     data.append('text_data', text_data);
//     var xhr = new XMLHttpRequest();
//     // xhr.open('POST', "http://localhost:8000", true);
//     xhr.open('POST', "http://localhost:5000/qr", true);
//     xhr.onload = function(){

//         if (xhr.status==403 || xhr.status==404) {
//             alert("Cannot send text data to the server!");
//         } else {
//             // alert(this.response);
//             print(this.response);
//             qrcode.src = data;
//         }
//     };
//     xhr.onreadystatechange = function() {
//         if (xhr.readyState == XMLHttpRequest.DONE) {
//             // alert(xhr.responseText);
//             alert('hi');
//             qrcode.src = "data:image/png;base64," + data;
//         }
//     }
//     xhr.send(data);
// }

function getQR() {
    $.ajax({
        type: "POST",
        // data: JSON.stringify(myData),
        // dataType: 'json',
        url: "http://localhost:5000/qr",
        data: {
            text_data: new Date().getTime()
        }
        }).done(
            function(mydata) {
                // alert(JSON.stringify(mydata));
                // $('.qr-container').html(data)
                $('.qrcode').attr("src", JSON.parse(mydata).src);
                // $('.qrcode').attr("src", "data:image/png;base64," + data).responseData);
            }
        );
}

// function getVideo() {

// }

function switchTab() {
    // $('#v-pills-user'.concat(user_id % 3)).tab('show');
    $('#v-pills-tab-user'.concat(user_id % 3)).tab('show');
    // alert('#v-pills-user'.concat(user_id % 3));
}


$('.qrcode').on('dblclick', function(){
    var email_title = "ICT.Open demo video from SURF";
    var email_body = "Hi there! You could download the demo video from ";
    email_body = email_body.concat(sharable_movie_link);
    email_body = email_body.concat(". The link is valid for 48 hours. Kind regards, SURF");
    // let email_body = "Hi there!<br>You could download the demo video from {1}.<br> The link is valid for 48 hours.<br>Kind regards, <br>SURF".formatUnicorn({1:video_link});
    var href_link = "mailto:user@example.com?subject=";
    href_link = href_link.concat(email_title);
    href_link = href_link.concat("&body=");
    href_link = href_link.concat(email_body);
    alert(email_body);
    window.location.href = href_link;
    // window.location.href = "mailto:user@example.com?subject={2}&body={3}".formatUnicorn({2:email_title, 3:email_body});
});

// Take a picture when cameraTrigger is tapped
cameraTrigger.onclick = function() {
    // cameraStart();
    // cameraOutput.classList.remove("taken");
    cameraSensor.width = cameraView.videoWidth;
    cameraSensor.height = cameraView.videoHeight;
    cameraSensor.getContext("2d").drawImage(cameraView, 0, 0);
    // cameraOutput.src = cameraSensor.toDataURL("image/webp");
    // cameraOutput.classList.add("taken");
    // track.pause();

    // Upload to server
    cameraSensor.toBlob(function(blob){
        var data = new FormData();
        data.append('upimage', blob);
        var xhr = new XMLHttpRequest();
        // xhr.open('POST', "http://localhost:8000", true);
        xhr.open('POST', "/server", true);
        xhr.onload = function(){
            if (xhr.status==403 || xhr.status==404) {
                alert("Cannot upload the camera image to the server!");
            } else {
                json_res = xhr.response
                // alert(json_res);
                json_res = JSON.parse(json_res)
                // alert(JSON.parse(json_res).src);
                $('.qrcode').attr("src", JSON.parse(json_res).src);
                user_list.push(JSON.parse(json_res).ts);
                qr_url_dict[user_id % 3] = JSON.parse(json_res).src;
                // $('#camera--output-user'.concat(user_id % 3)).removeClass('taken');
                $('#camera--output-user'.concat(user_id % 3)).attr("visibility", "visible");
                $('#camera--output-user'.concat(user_id % 3)).attr("src", cameraSensor.toDataURL("image/webp"));
                // $('#camera--output-user'.concat(user_id % 3)).addClass('taken');
                user_id++;
            }
        };
        xhr.send(data);
    });

    // request QR code
    // requestQRCode('some text');
    // getQR();
    switchTab();
};

// Start the video stream when the window loads
window.addEventListener("load", cameraStart, false);
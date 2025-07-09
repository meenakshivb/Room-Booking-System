'use strict';

// import firebase
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js';
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js';

// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
	apiKey: "AIzaSyCDNdmi0i44tdeKDSHmLurXDR7UAy35PLI",
	authDomain: "hale-mercury-417714.firebaseapp.com",
	projectId: "hale-mercury-417714",
	storageBucket: "hale-mercury-417714.appspot.com",
	messagingSenderId: "617584980706",
	appId: "1:617584980706:web:7a8591cc836a6e5a0064bb"
  };
  
window.addEventListener("load", function () {
	const app = initializeApp(firebaseConfig);
	const auth = getAuth(app);
	updateUI(document.cookie);
	console.log("Electric Vehicles");
	// signup of a new user to firebase

	document.getElementById("sign-up").addEventListener('click', function () {
		const email = document.getElementById("email").value
		const password = document.getElementById("password").value

		createUserWithEmailAndPassword(auth, email, password)
			.then((userCredential) => {
				// we have a created user
				const user = userCredential.user;

				user.getIdToken().then((token) => {
					document.cookie = "token=" + token + "; path=/; SameSite=Strict";
					window.location = "/";
				});
			})
			// get the id token for the user who just logged in and force a redirect to /
			.catch((error) => {
				// issue with signup that we will drop to console
				console.log(error.code + error.message);
			})
	})

	// login of a user to firebase
	document.getElementById("login").addEventListener('click', function () {
		const email = document.getElementById("email").value
		const password = document.getElementById("password").value

		signInWithEmailAndPassword(auth, email, password)
			.then((userCredential) => {
				const user = userCredential.user;
				console.log("logged in");

				user.getIdToken().then((token) => {
					document.cookie = "token=" + token + "; path=/; SameSite=Strict";
					window.location = "/";
				});
			})
			.catch((error) => {
				console.log(error.code + error.message);
			})
	})

	document.getElementById("sign-out").addEventListener('click', function () {
		signOut(auth)
			.then((output) => {
				document.cookie = "token=;path=/; SameSite=Strict";
				window.location = "/";
			})
	})
})

function updateUI(cookie) {
	var token = parseCookieToken(cookie);
	if (token.length > 0) {
		document.getElementById("login-box").hidden = true;
		document.getElementById("sign-out").hidden = false;
	} else {
		document.getElementById("login-box").hidden = false;
		document.getElementById("sign-out").hidden = true;
	}
};

function parseCookieToken(cookie) {
	var strings = cookie.split(';');

	for (let i = 0; i < strings.length; i++) {
		var temp = strings[i].split('=');
		if (temp[0] == "token")
			return temp[1];
	}
	return "";
};


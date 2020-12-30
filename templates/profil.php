<!DOCTYPE html>
<html>

<head>
	<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />

<link
rel="stylesheet"
href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh"
crossorigin="anonymous"
>
	<title>Page de profil</title>
	<link rel="stylesheet" type="text/css" media="screen" href=../static/styles/base.css>

</head>

<body>
	 <div class="container-fluid">
      <div class="row">
        <nav class="col navbar navbar-expand-lg navbar-dark">
          <a class="navbar-brand">CF</a>
          <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div id="navbarContent" class="collapse navbar-collapse">
            <ul class="navbar-nav">
              <li class="nav-item">
                <a class="nav-link" href="">Accueil</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="#">Qui sommes-nous?</a>
              </li>
                 <li class="nav-item active">
                <a class="nav-link" href="#">Mon profil</a>
              </li>
               </li>
                 <li class="nav-item">
                <a class="nav-link" href="{{url_for('compa')}}">Mes compatibilités</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="{{ url_for('signout') }}">Se déconnecter</a>
              </li>
            </ul>
          </div>
        </nav>
      </div>
    </div>
  </div>

	<h1> {{ user.firstname }} </h1>
	<img class="rounded-circle account-img" src="{{ image_file }}">	
	<p> {{ user.description }} </p>
	<p> {{ user.recherche }} </p>

	<?php
	$x=2;
	$y=3;
	if ($x>$y) ?>
	{<p> <a href={{url_for('modifprofil')}}> Modifier mon profil </a></p>; 
}
	
}
</body>

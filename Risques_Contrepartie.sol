// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GestionRisqueContrepartie {
    struct Contrepartie {
        address portefeuille;
        uint256 scoreCredit;
        uint256 limiteExposition;
        uint256 expositionCourante;
        uint256 collaterale; // Montant du collatéral
        uint256 probabiliteDefaut; // Probabilité de défaut (PD) en pourcentage
        uint256 pertesEnCasDeDefaut; // Pertes en cas de défaut (LGD) en pourcentage
    }

    mapping(address => Contrepartie) public contreparties;

    // Événements pour signaler des dépassements ou des mises à jour importantes
    event ContrepartieAjoutee(address indexed portefeuille, uint256 limiteExposition);
    event ExpositionMiseAJour(address indexed portefeuille, uint256 nouvelleExposition);
    event LimiteDepassee(address indexed portefeuille, uint256 exposition);

    // Ajouter une contrepartie
    function ajouterContrepartie(
        address _portefeuille,
        uint256 _scoreCredit,
        uint256 _limiteExposition,
        uint256 _probabiliteDefaut,
        uint256 _pertesEnCasDeDefaut,
        uint256 _collaterale
    ) public {
        require(contreparties[_portefeuille].portefeuille == address(0), "Contrepartie deja enregistree");
        require(_scoreCredit > 0 && _limiteExposition > 0, "Score de credit et limite doivent etre positifs");

        contreparties[_portefeuille] = Contrepartie({
            portefeuille: _portefeuille,
            scoreCredit: _scoreCredit,
            limiteExposition: _limiteExposition,
            expositionCourante: 0,
            collaterale: _collaterale,
            probabiliteDefaut: _probabiliteDefaut,
            pertesEnCasDeDefaut: _pertesEnCasDeDefaut
        });

        emit ContrepartieAjoutee(_portefeuille, _limiteExposition);
    }

    // Mettre à jour l'exposition d'une contrepartie
    function mettreAJourExposition(address _portefeuille, uint256 _nouvelleExposition) public {
        Contrepartie storage contrepartie = contreparties[_portefeuille];
        require(contrepartie.portefeuille != address(0), "Contrepartie non trouvee");
        require(_nouvelleExposition >= 0, "Exposition ne peut pas etre negative");

        contrepartie.expositionCourante = _nouvelleExposition;
        emit ExpositionMiseAJour(_portefeuille, _nouvelleExposition);

        // Émettre un événement si la limite est dépassée
        if (contrepartie.expositionCourante > contrepartie.limiteExposition) {
            emit LimiteDepassee(_portefeuille, contrepartie.expositionCourante);
        }
    }

    // Calculer le risque pour une contrepartie
    function calculerRisque(address _portefeuille) public view returns (uint256) {
        Contrepartie memory contrepartie = contreparties[_portefeuille];
        require(contrepartie.portefeuille != address(0), "Contrepartie non trouvee");

        // Calcul du score de risque : (Exposition Courante / Limite Exposition) * (100 / Score Crédit)
        if (contrepartie.limiteExposition == 0) {
            return 0; // Éviter la division par zéro
        }
        return (contrepartie.expositionCourante * 10000) / (contrepartie.limiteExposition * contrepartie.scoreCredit);
    }

    // Calculer le ratio de couverture
    function calculerRatioCouverture(address _portefeuille) public view returns (uint256) {
        Contrepartie memory contrepartie = contreparties[_portefeuille];
        require(contrepartie.portefeuille != address(0), "Contrepartie non trouvee");

        if (contrepartie.expositionCourante == 0) {
            return 0; // Éviter la division par zéro
        }

        // Ratio de couverture = (Collatéral / Exposition Courante) * 100
        return (contrepartie.collaterale * 100) / contrepartie.expositionCourante;
    }

    // Calculer les pertes attendues
    function calculerPertesAttendues(address _portefeuille) public view returns (uint256) {
        Contrepartie memory contrepartie = contreparties[_portefeuille];
        require(contrepartie.portefeuille != address(0), "Contrepartie non trouvee");

        // Pertes Attendues = Exposition * Probabilité de Défaut (PD) * Pertes en Cas de Défaut (LGD)
        return (contrepartie.expositionCourante * contrepartie.probabiliteDefaut * contrepartie.pertesEnCasDeDefaut) / 10000;
    }
}
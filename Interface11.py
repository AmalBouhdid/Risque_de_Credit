import streamlit as st
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os

# Page configuration
st.set_page_config(
    page_title="Gestion des Risques Contreparties",
    page_icon="🛡",
    layout="wide"
)

# Custom CSS
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #4682B4;
        color: white;
        border-radius: 8px;
    }
    .stHeader {
        color: #4CAF50;
    }
    .stSuccess {
        color: #28a745;
    }
    .stError {
        color: #dc3545;
    }
    </style>
    """, unsafe_allow_html=True
)

# Load environment variables
load_dotenv()

# Connect to Infura
infura_url = "https://polygon-amoy.infura.io/v3/595d73c2252c4182a943f36cbd96fd0b"
web3 = Web3(Web3.HTTPProvider(infura_url))

# Sidebar navigation
st.sidebar.image("Black_White_Simple_Wedding_Welcome_Poster__1_-removebg-preview.png", use_container_width=True)  
st.sidebar.title("➕ 🔄 📊 📄")
menu_option = st.sidebar.radio(
    "Sélectionnez une option ci-dessous:",
    ("Accueil", "Ajouter une Contrepartie", "Mettre à Jour", "Calcul des Risques", "Informations")
)

# Check connection
if web3.is_connected():
    st.success("✅ Connecté à Ethereum via Infura")
else:
    st.error("❌ Échec de la connexion à Infura")
    st.stop()

# Load private key
private_key = os.getenv("PRIVATE_KEY")
if not private_key:
    st.error("🔒 Clé privée introuvable ! Veuillez l'ajouter au fichier .env.")
    st.stop()

# Wallet details
account = Account.from_key(private_key)
portefeuille = account.address
st.info(f"🔑 Adresse du portefeuille : {portefeuille}")

# Smart Contract details
contract_address = Web3.to_checksum_address("0x70c68a1006a2780831fc6bed8ef1087ea95a4e18")
contract_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "_portefeuille", "type": "address"},
            {"internalType": "uint256", "name": "_scoreCredit", "type": "uint256"},
            {"internalType": "uint256", "name": "_limiteExposition", "type": "uint256"},
            {"internalType": "uint256", "name": "_probabiliteDefaut", "type": "uint256"},
            {"internalType": "uint256", "name": "_pertesEnCasDeDefaut", "type": "uint256"},
            {"internalType": "uint256", "name": "_collaterale", "type": "uint256"}
        ],
        "name": "ajouterContrepartie",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_portefeuille", "type": "address"},
            {"internalType": "uint256", "name": "_nouvelleExposition", "type": "uint256"}
        ],
        "name": "mettreAJourExposition",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "_portefeuille", "type": "address"}],
        "name": "calculerRisque",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "_portefeuille", "type": "address"}],
        "name": "calculerRatioCouverture",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "_portefeuille", "type": "address"}],
        "name": "calculerPertesAttendues",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "contreparties",
		"outputs": [
			{
				"internalType": "address",
				"name": "portefeuille",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "scoreCredit",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "limiteExposition",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "expositionCourante",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "collaterale",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "probabiliteDefaut",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "pertesEnCasDeDefaut",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# Helper function to send transactions
def send_transaction(txn_function, *args, gas=300000):
    try:
        # Prepare the transaction
        nonce = web3.eth.get_transaction_count(portefeuille)
        txn = txn_function(*args).build_transaction({
            "from": portefeuille,
            "nonce": nonce,
            "gas": gas,
            "gasPrice": web3.to_wei("30", "gwei")
        })

        # Sign and send the transaction
        signed_txn = web3.eth.account.sign_transaction(txn, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # Wait for the receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        # Check transaction status
        if receipt['status'] == 1:
            return {"success": True, "tx_hash": tx_hash.hex()}
        else:
            # If failed, try to decode the revert reason
            revert_reason = get_revert_reason(tx_hash)
            return {"success": False, "revert_reason": revert_reason}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_revert_reason(tx_hash):
    try:
        # Get the transaction details
        tx = web3.eth.get_transaction(tx_hash)
        # Simulate the transaction to fetch the revert reason
        revert_data = web3.eth.call({
            "to": tx["to"],
            "data": tx["input"],
            "from": tx["from"]
        }, tx["blockNumber"])
        return web3.to_text(revert_data)
    except Exception:
        return "Exposition depasse la limite autorisee."


# Main Menu Options
if menu_option == "Accueil":
    st.image("White Minimalist Profile LinkedIn Banner.png", use_container_width=True)
    st.markdown("<h2 style='text-align: center; color: #4682b4'>Bienvenue</h2>", unsafe_allow_html=True)
    st.write(
         "Bienvenue dans l'application *Gestion des Risques Contreparties*, une solution innovante basée sur la blockchain "
         "pour gérer les risques financiers associés à vos contreparties. Cette plateforme offre des outils puissants et "
         "sécurisés pour automatiser vos calculs de risques et rationaliser vos opérations."
)
    st.markdown("<h2 style='color: #4682b4;'>Fonctionnalités</h2>", 
    unsafe_allow_html=True)
    st.markdown("""
         - **🔍 Suivi des Contreparties** : Ajoutez, consultez et mettez à jour les informations financières de vos contreparties.
         - **📈 Calcul des Risques** : Évaluez les risques en analysant des indicateurs clés tels que le ratio de couverture et les pertes attendues.
         - **⚙️ Automatisation Sécurisée** : Gérez les expositions financières et suivez les performances grâce à des contrats intelligents déployés sur Ethereum.
         - **📊 Analyse en Temps Réel** : Obtenez des rapports instantanés pour des prises de décision rapides et informées.
""")
    st.markdown("<h2 style='color: #4682b4;'>Pourquoi cette application ?</h2>", 
    unsafe_allow_html=True)
    st.markdown("""
         - **Fiabilité** : Basée sur la blockchain Ethereum, vos données sont sécurisées et immuables.
         - **Simplicité** : Une interface claire et intuitive pour une gestion simplifiée.
         - **Innovation** : Exploitez la puissance des contrats intelligents pour automatiser vos processus financiers.
""")
    st.markdown("<h2 style='color: #4682b4;'>Comment utiliser l'application ?</h2>", 
    unsafe_allow_html=True)
    st.markdown("""
    1. Accédez aux différentes sections via le menu latéral :
         - **Accueil** : Vue d'ensemble de l'application.
         - **Ajouter une Contrepartie** : Enregistrez de nouvelles contreparties avec leurs données financières.
         - **Mettre à Jour** : Mettez à jour les expositions ou les données associées à une contrepartie.
         - **Calcul des Risques** : Évaluez les pertes attendues et analysez vos ratios de couverture.
        - **Informations** : Consultez des données supplémentaires ou des rapports détaillés.
""")
    st.markdown("<h2 style='color: #4682b4;'>Prêt à démarrer ?</h2>", 
    unsafe_allow_html=True)
    st.write("Commencez dès maintenant en sélectionnant une action dans le menu latéral.🚀")
    st.markdown("**Votre sécurité financière commence ici.**")
 
 
    

elif menu_option == "Ajouter une Contrepartie":
    st.image("White Minimalist Profile LinkedIn Banner.png", use_container_width=True)
    st.markdown("<h2 style='color: #4682B4;'>➕ Ajouter une Contrepartie</h2>", unsafe_allow_html=True)
    import streamlit as st


    col1, col2 = st.columns(2)

    with col1:
        score_credit = st.number_input("Score de Crédit", min_value=1, value=100)
        limite_exposition = st.number_input("Limite d'Exposition", min_value=1, value=1000)

    with col2:
        probabilite_defaut = st.number_input("Probabilité de Défaut (%)", min_value=0, max_value=100, value=10)
        pertes_defaut = st.number_input("Pertes en Cas de Défaut (%)", min_value=0, max_value=100, value=50)
        nouveau_collateral = st.number_input("Nouveau Collateral", min_value=0, value=0)

    if st.button("Ajouter Contrepartie"):
        tx_hash = send_transaction(
            contract.functions.ajouterContrepartie,
            portefeuille,
            int(score_credit),
            int(limite_exposition),
            int(probabilite_defaut),
            int(pertes_defaut),
            int(nouveau_collateral)
        )
        if tx_hash:
            st.success(f"✅ Contrepartie ajoutée ! Hash: {tx_hash}")
        else:
            st.error("❌ Échec de la transaction.")



elif menu_option == "Mettre à Jour":
    st.image("White Minimalist Profile LinkedIn Banner.png", use_container_width=True)
    st.markdown("<h2 style='color: #4682B4;'>🔄 Mettre à Jour les Données</h2>", unsafe_allow_html=True)

    st.subheader("Mettre à Jour l'Exposition")
    nouvelle_exposition = st.number_input("Nouvelle Exposition", min_value=0, value=0)
    if st.button("Mettre à Jour Exposition"):
        tx_hash = send_transaction(
            contract.functions.mettreAJourExposition,
            portefeuille,
            int(nouvelle_exposition)
        )
        if tx_hash:
            st.success(f"✅ Exposition mise à jour ! Hash: {tx_hash}")
        else:
            st.error("❌ Échec de la mise à jour.")

elif menu_option == "Calcul des Risques":
    st.image("White Minimalist Profile LinkedIn Banner.png", use_container_width=True)
    st.markdown("<h2 style='color: #4682B4;'>📊 Calcul des Risques et Ratios</h2>", unsafe_allow_html=True)
    if st.button("Calculer"):
        try:
            risque = contract.functions.calculerRisque(portefeuille).call()
            ratio_couverture = contract.functions.calculerRatioCouverture(portefeuille).call()
            pertes_attendues = contract.functions.calculerPertesAttendues(portefeuille).call()

            st.metric(label="Score de Risque", value=f"{risque}")
            st.metric(label="Ratio de Couverture", value=f"{ratio_couverture}%")
            st.metric(label="Pertes Attendues", value=f"{pertes_attendues}")

        except Exception as e:
            st.error(f"Erreur lors du calcul des risques : {e}")

elif menu_option == "Informations":
    st.image("White Minimalist Profile LinkedIn Banner.png", use_container_width=True)
    st.markdown("<h2 style='color: #4682B4;'>📄 Informations sur la Contrepartie</h2>", unsafe_allow_html=True)
    if st.button("Afficher Informations"):
        try: 
            contrepartie_info = contract.functions.contreparties(portefeuille).call()
            if contrepartie_info[0] != "0x0000000000000000000000000000000000000000":
                st.json({
                    "Portefeuille": contrepartie_info[0],
                    "Score de Crédit": contrepartie_info[1],
                    "Limite d'Exposition": contrepartie_info[2],
                    "Exposition Courante": contrepartie_info[3],
                    "Collateral": contrepartie_info[4],
                    "Probabilité de Défaut": contrepartie_info[5],
                    "Pertes en Cas de Défaut": contrepartie_info[6]
                })
            else:
                st.warning("Aucune contrepartie trouvée.")
        except Exception as e:
            st.error(f"Erreur : {e}")

# Footer
st.markdown("---")
st.info("💡 Note : Utilisez toujours des réseaux de test pour vos expérimentations.")

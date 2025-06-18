// neo4j_exploration/populate_sample_graph.cypher
MATCH (n) DETACH DELETE n;

// --- Create Nodes ---

// User
CREATE (user1:User {userId: 1, email: 'weijie@example.com', name: 'Zhu Weijie'});

// Assets
CREATE (asset1:Asset {assetId: 101, symbol: 'AAPL', name: 'Apple Inc.', type: 'stock'});
CREATE (asset2:Asset {assetId: 102, symbol: 'BTC', name: 'Bitcoin', type: 'crypto'});
CREATE (asset3:Asset {assetId: 103, symbol: 'MSFT', name: 'Microsoft Corp.', type: 'stock'});

// Portfolio Holdings for User1
CREATE (holding1:PortfolioHolding {holdingId: 201, quantity: 10, purchase_price: 150.00, purchase_date: date("2025-01-10")});
CREATE (holding2:PortfolioHolding {holdingId: 202, quantity: 0.5, purchase_price: 30000.00, purchase_date: date("2025-02-15")});
CREATE (holding3:PortfolioHolding {holdingId: 203, quantity: 5, purchase_price: 160.00, purchase_date: date("2025-03-20")});

// --- Create Relationships ---

// User1 OWNS Holding1 (AAPL)
MATCH (u:User {userId: 1}), (h:PortfolioHolding {holdingId: 201})
CREATE (u)-[:OWNS]->(h);

// User1 OWNS Holding2 (BTC)
MATCH (u:User {userId: 1}), (h:PortfolioHolding {holdingId: 202})
CREATE (u)-[:OWNS]->(h);

// User1 OWNS Holding3 (AAPL, second lot)
MATCH (u:User {userId: 1}), (h:PortfolioHolding {holdingId: 203})
CREATE (u)-[:OWNS]->(h);

// Holding1 IS_FOR_ASSET Asset1 (AAPL)
MATCH (h:PortfolioHolding {holdingId: 201}), (a:Asset {assetId: 101})
CREATE (h)-[:IS_FOR_ASSET]->(a);

// Holding2 IS_FOR_ASSET Asset2 (BTC)
MATCH (h:PortfolioHolding {holdingId: 202}), (a:Asset {assetId: 102})
CREATE (h)-[:IS_FOR_ASSET]->(a);

// Holding3 IS_FOR_ASSET Asset1 (AAPL)
MATCH (h:PortfolioHolding {holdingId: 203}), (a:Asset {assetId: 101})
CREATE (h)-[:IS_FOR_ASSET]->(a);

CALL db.awaitIndexes();
RETURN "Sample Alpha-Dash graph created successfully!" AS status;

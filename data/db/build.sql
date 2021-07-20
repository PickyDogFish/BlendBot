CREATE TABLE IF NOT EXISTS users (
    userID integer PRIMARY KEY NOT NULL,
    msgXP integer DEFAULT 0,
    renderXP integer DEFAULT 0,
    XPLock text DEFAULT CURRENT_TIMESTAMP,
    isInServer boolean DEFAULT 1
);

CREATE TABLE IF NOT EXISTS submission (
    userID integer,
    msgID integer PRIMARY KEY NOT NULL,
    votingMsgID integer,
    challengeID integer NOT NULL,
    FOREIGN KEY (challengeID) REFERENCES challenges (challengeID)

    FOREIGN KEY (userID) REFERENCES users (userID)
);

CREATE TABLE IF NOT EXISTS votes (
    votingMsgID integer,
    voterID integer,
    vote integer DEFAULT 0,
	PRIMARY KEY (votingMsgID, voterID),
	FOREIGN KEY (VotingMsgID) REFERENCES submissions (votingMsgID),
    FOREIGN KEY (voterID) REFERENCES users (userID)
);

CREATE TABLE IF NOT EXISTS challengeTypes (
    challengeTypeID integer PRIMARY KEY,
    challengeTypeDescription text
);

CREATE TABLE IF NOT EXISTS themes (
    themeName text PRIMARY KEY,
    themeStatus integer DEFAULT 0,
    lastUsed datetime DEFAULT "2011-11-11 00:00:00"
);

CREATE TABLE IF NOT EXISTS challenge (
    challengeTypeID integer DEFAULT 0,
    themeName text NOT NULL,
    challengeID integer PRIMARY KEY AUTOINCREMENT NOT NULL,
    startDate datetime NOT NULL,
    endDate datetime NOT NULL,
    FOREIGN KEY (themeName) REFERENCES themes (themeName)
    FOREIGN KEY (challengeTypeID) REFERENCES challengeTypes (challengeTypeID)
);

CREATE TABLE IF NOT EXISTS currentChallenge (
    currentChallengeID integer,
    previousChallengeID integer,
    challengeTypeID integer PRIMARY KEY,
    FOREIGN KEY (currentChallengeID) REFERENCES challenge (challengeID),
    FOREIGN KEY (previousChallengeID) REFERENCES challenge (challengeID), 
    FOREIGN KEY (challengeTypeID) REFERENCES challengeTypes (challengeTypeID)
);

INSERT OR IGNORE INTO challengeTypes (challengeTypeID, challengeTypeDescription) VALUES (0, "Daily challenge"), (1, "Weekly challenge");

INSERT OR IGNORE INTO themes (themeName, themeStatus) VALUES ("placeholder", 0);

INSERT OR IGNORE INTO challenge (challengeID, themeName, startDate, endDate) VALUES (0, "placeholder", "2011-11-11 00:00:00", "2011-11-11 00:00:00");

INSERT OR IGNORE INTO currentChallenge (currentChallengeID, previousChallengeID, challengeTypeID) VALUES (0,0,0);



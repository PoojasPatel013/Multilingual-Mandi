# The Multilingual Mandi

## Overview

The Multilingual Mandi is a web-based platform that bridges language barriers in local trade through real-time AI-powered translation, intelligent price discovery, and culturally-aware negotiation assistance. The system architecture emphasizes real-time communication, scalable AI services, and responsive web interfaces to create seamless multilingual commerce experiences.

The platform serves three primary user types: local vendors managing their digital storefronts, customers browsing and negotiating across language barriers, and market administrators overseeing platform operations. The system integrates multiple AI services including neural machine translation, market analysis algorithms, and cultural context engines to facilitate fair and efficient trade.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        VD[Vendor Dashboard]
        CI[Customer Interface]
        MA[Market Admin Panel]
    end
    
    subgraph "API Gateway"
        AG[API Gateway/Load Balancer]
    end
    
    subgraph "Application Services"
        AS[Authentication Service]
        CS[Communication Service]
        PS[Product Service]
        NS[Negotiation Service]
        AS2[Analytics Service]
    end
    
    subgraph "AI Services"
        TE[Translation Engine]
        PDS[Price Discovery System]
        NA[Negotiation Assistant]
        CCE[Cultural Context Engine]
    end
    
    subgraph "External Services"
        TPI[Translation Provider APIs]
        PG[Payment Gateways]
        MDS[Market Data Sources]
    end
    
    subgraph "Data Layer"
        PDB[(Primary Database)]
        RDB[(Redis Cache)]
        FS[File Storage]
    end
    
    VD --> AG
    CI --> AG
    MA --> AG
    
    AG --> AS
    AG --> CS
    AG --> PS
    AG --> NS
    AG --> AS2
    
    CS --> TE
    PS --> PDS
    NS --> NA
    NS --> CCE
    
    TE --> TPI
    PDS --> MDS
    NS --> PG
    
    AS --> PDB
    CS --> RDB
    PS --> PDB
    NS --> PDB
    AS2 --> PDB
    
    PS --> FS
```

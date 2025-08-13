# Overview

This is a Telegram-based economic simulation game built in Python. Players can build businesses, manage farms, engage in PvP battles, and participate in special events while managing their virtual economy. The game features a comprehensive progression system with VIP tiers, real-money payments, and competitive leaderboards.

# User Preferences

Preferred communication style: Simple, everyday language.
Language: Russian - user prefers documentation and communication in Russian.

# System Architecture

## Core Game Framework
- **Flask Application**: Central web framework handling database connections and application context
- **SQLAlchemy ORM**: Database abstraction layer with declarative base models
- **Threading Model**: Background tasks run in separate daemon threads for game engine operations and event scheduling

## Bot Architecture
- **Telegram Bot API**: Python-telegram-bot library handling all user interactions
- **Modular System Design**: Game logic separated into specialized systems (Economic, PvP, Events, Payment)
- **Handler-Based Routing**: Command handlers, callback query handlers, and message handlers for different user inputs

## Database Schema
- **Player Model**: Core user data including coins, energy, level, VIP status, and statistics
- **Business/Farm Models**: Player-owned assets with income generation and timing mechanics
- **Transaction Model**: Financial activity logging for all monetary operations
- **PvP Battle Model**: Combat records and battle history
- **Game Event Model**: Special events and promotions

## Game Systems
- **Energy System**: Time-based regeneration limiting player actions
- **Business Income**: Automated passive income generation with collection mechanics
- **Farm Management**: Crop planting and harvesting with different time cycles
- **PvP Combat**: Player-vs-player battles with coin stealing mechanics
- **Experience/Leveling**: Progression system with level-based restrictions
- **VIP System**: Premium subscriptions with gameplay benefits

## Background Processing
- **Game Engine**: Continuous background thread updating player energy and processing business income
- **Event Scheduler**: Automated creation and management of special game events
- **Leaderboard Updates**: Regular calculation and updating of competitive rankings
- **Data Cleanup**: Periodic removal of old transactions and expired data

## Security & Rate Limiting
- **Rate Limiting**: Per-user action throttling to prevent abuse
- **Activity Logging**: Comprehensive tracking of player actions for analysis
- **Suspicious Activity Detection**: Automated monitoring for unusual behavior patterns
- **User Blocking**: Capability to block problematic users

## Localization
- **Multi-language Support**: Russian language implementation with extensible framework
- **Message Templates**: Centralized text management for consistent messaging
- **Dynamic Content**: Runtime text generation with variable substitution

# External Dependencies

## Telegram Integration
- **python-telegram-bot**: Official Telegram Bot API wrapper
- **Telegram Payments API**: Processing real-money transactions through Telegram

## Database
- **SQLAlchemy**: Database ORM and connection management
- **SQLite/PostgreSQL**: Database engines (SQLite for development, configurable for production)

## Payment Processing
- **Telegram Payments**: Built-in payment processing through Telegram's payment system
- **Provider Token**: External payment provider integration

## Infrastructure
- **Flask**: Web application framework
- **Python Threading**: Background task processing
- **Environment Variables**: Configuration management through OS environment

## Development Tools
- **Python Logging**: Comprehensive logging system
- **JSON**: Data serialization for complex objects
- **Random/Math Libraries**: Game mechanics calculations
- **DateTime**: Time-based game feature management
#!/usr/bin/env python3
"""
Reset and seed all 100 domains in the database
Run this script to clear existing domains and add all 100 new ones
"""

from app import app, db, Domain

def reset_domains():
    """Clear all domains and reseed with 100 domains"""
    with app.app_context():
        print("Starting domain reset...")
        
        # Delete all existing domains
        deleted = Domain.query.delete()
        print(f"Deleted {deleted} existing domains")
        
        # Commit the deletion
        db.session.commit()
        print("Database cleared")
        
        # The domains will be automatically seeded on next app run
        # Or we can seed them directly here
        domains_data = [
            # Top 100 High-Demand Tech Domains
            {'name': 'Machine Learning', 'description': 'AI/ML models, neural networks, deep learning, NLP, computer vision', 'icon': '🧠', 'keywords': 'tensorflow, pytorch, scikit-learn, nlp, cv, neural'},
            {'name': 'Python Programming', 'description': 'Core Python, data structures, automation, scripting, libraries', 'icon': '🐍', 'keywords': 'python, pandas, numpy, scripting, automation, oop'},
            {'name': 'Web Development (MERN)', 'description': 'Full-stack web apps with MongoDB, Express, React, Node.js', 'icon': '🌐', 'keywords': 'react, nodejs, express, mongodb, javascript, fullstack'},
            {'name': 'Flask Backend', 'description': 'Build APIs, microservices, and backend systems with Flask', 'icon': '🌶️', 'keywords': 'flask, sqlalchemy, api, backend, microservices, rest'},
            {'name': 'Data Science', 'description': 'Data analysis, visualization, statistical modeling, business intelligence', 'icon': '📊', 'keywords': 'pandas, matplotlib, sql, statistics, analytics, bi'},
            {'name': 'Cloud & DevOps', 'description': 'AWS, Docker, Kubernetes, CI/CD, infrastructure automation', 'icon': '☁️', 'keywords': 'aws, docker, kubernetes, ci-cd, terraform, devops'},
            {'name': 'Mobile Development', 'description': 'iOS, Android, React Native, Flutter app development', 'icon': '📱', 'keywords': 'ios, android, react native, flutter, mobile'},
            {'name': 'Database Design', 'description': 'SQL, NoSQL, schema design, optimization, querying', 'icon': '🗄️', 'keywords': 'sql, mongodb, postgres, mysql, database, schema'},
            {'name': 'Cybersecurity', 'description': 'Network security, encryption, penetration testing, secure coding', 'icon': '🔐', 'keywords': 'security, encryption, hacking, networks, ssl, auth'},
            {'name': 'Blockchain & Web3', 'description': 'Cryptocurrency, smart contracts, blockchain technology, DeFi', 'icon': '⛓️', 'keywords': 'blockchain, crypto, solidity, defi, nft, web3'},
            # 11-20
            {'name': 'Artificial Intelligence', 'description': 'AI fundamentals, expert systems, cognitive computing, AI ethics', 'icon': '🤖', 'keywords': 'ai, cognitive, expert systems, agi, ethics'},
            {'name': 'Java Programming', 'description': 'Enterprise Java, Spring Boot, microservices, JVM optimization', 'icon': '☕', 'keywords': 'java, spring, jvm, maven, gradle, enterprise'},
            {'name': 'JavaScript Mastery', 'description': 'Modern JS, ES6+, async programming, design patterns', 'icon': '⚡', 'keywords': 'javascript, es6, async, promises, patterns'},
            {'name': 'TypeScript', 'description': 'Static typing, interfaces, generics, advanced TypeScript patterns', 'icon': '🔷', 'keywords': 'typescript, types, interfaces, generics'},
            {'name': 'React.js', 'description': 'Component architecture, hooks, state management, performance', 'icon': '⚛️', 'keywords': 'react, hooks, redux, context, jsx'},
            {'name': 'Angular', 'description': 'Enterprise Angular apps, RxJS, services, dependency injection', 'icon': '🅰️', 'keywords': 'angular, rxjs, typescript, spa, components'},
            {'name': 'Vue.js', 'description': 'Progressive framework, Vuex, composition API, Nuxt.js', 'icon': '🟢', 'keywords': 'vue, vuex, nuxt, composition, sfc'},
            {'name': 'Node.js Backend', 'description': 'Server-side JavaScript, Express, APIs, real-time apps', 'icon': '🟩', 'keywords': 'nodejs, express, npm, event-loop, async'},
            {'name': 'Django Framework', 'description': 'Python web framework, ORM, MVT, RESTful APIs', 'icon': '🎸', 'keywords': 'django, orm, rest, python, mvt'},
            {'name': 'FastAPI', 'description': 'Modern Python API framework, async, auto documentation', 'icon': '⚡', 'keywords': 'fastapi, async, python, openapi, pydantic'},
            # 21-30
            {'name': 'Ruby on Rails', 'description': 'Full-stack framework, MVC, ActiveRecord, rapid development', 'icon': '💎', 'keywords': 'rails, ruby, mvc, activerecord, gems'},
            {'name': 'Go Programming', 'description': 'Golang, concurrency, microservices, system programming', 'icon': '🐹', 'keywords': 'golang, goroutines, concurrency, performance'},
            {'name': 'Rust Programming', 'description': 'Memory safety, systems programming, performance, WebAssembly', 'icon': '🦀', 'keywords': 'rust, memory, ownership, wasm, systems'},
            {'name': 'C++ Programming', 'description': 'Modern C++, STL, templates, performance optimization', 'icon': '⚙️', 'keywords': 'cpp, stl, templates, performance, memory'},
            {'name': 'C# & .NET', 'description': '.NET Core, ASP.NET, Entity Framework, Azure integration', 'icon': '🔵', 'keywords': 'csharp, dotnet, asp, ef, azure'},
            {'name': 'Kotlin Development', 'description': 'Android development, coroutines, multiplatform', 'icon': '🎯', 'keywords': 'kotlin, android, coroutines, jvm, multiplatform'},
            {'name': 'Swift & iOS', 'description': 'iOS app development, SwiftUI, UIKit, App Store publishing', 'icon': '🍎', 'keywords': 'swift, ios, swiftui, uikit, xcode'},
            {'name': 'Flutter Development', 'description': 'Cross-platform apps, Dart, widgets, state management', 'icon': '🦋', 'keywords': 'flutter, dart, widgets, crossplatform, material'},
            {'name': 'React Native', 'description': 'Mobile apps with React, native modules, performance', 'icon': '📲', 'keywords': 'reactnative, javascript, mobile, expo, native'},
            {'name': 'SQL Mastery', 'description': 'Advanced queries, optimization, indexing, stored procedures', 'icon': '🗃️', 'keywords': 'sql, queries, optimization, joins, indexing'},
            # 31-40
            {'name': 'PostgreSQL', 'description': 'Advanced PostgreSQL, JSONB, full-text search, replication', 'icon': '🐘', 'keywords': 'postgres, sql, jsonb, replication, pgadmin'},
            {'name': 'MongoDB', 'description': 'NoSQL database, aggregation, sharding, replica sets', 'icon': '🍃', 'keywords': 'mongodb, nosql, aggregation, sharding, atlas'},
            {'name': 'Redis & Caching', 'description': 'In-memory databases, caching strategies, pub/sub', 'icon': '🔴', 'keywords': 'redis, cache, inmemory, pubsub, performance'},
            {'name': 'GraphQL', 'description': 'Query language, Apollo, schema design, subscriptions', 'icon': '🔷', 'keywords': 'graphql, apollo, queries, schema, subscriptions'},
            {'name': 'REST API Design', 'description': 'RESTful principles, API security, documentation, versioning', 'icon': '🔌', 'keywords': 'rest, api, http, swagger, endpoints'},
            {'name': 'AWS Cloud', 'description': 'EC2, S3, Lambda, RDS, CloudFormation, serverless', 'icon': '☁️', 'keywords': 'aws, ec2, lambda, s3, cloud, serverless'},
            {'name': 'Azure Cloud', 'description': 'Azure services, DevOps, Functions, App Services', 'icon': '🔷', 'keywords': 'azure, cloud, devops, functions, microsoft'},
            {'name': 'Google Cloud Platform', 'description': 'GCP services, App Engine, BigQuery, Kubernetes Engine', 'icon': '☁️', 'keywords': 'gcp, google, cloud, bigquery, kubernetes'},
            {'name': 'Docker Containerization', 'description': 'Containers, images, Docker Compose, orchestration', 'icon': '🐳', 'keywords': 'docker, containers, compose, images, orchestration'},
            {'name': 'Kubernetes', 'description': 'Container orchestration, pods, services, deployments', 'icon': '⚓', 'keywords': 'kubernetes, k8s, orchestration, pods, helm'},
            # 41-50
            {'name': 'CI/CD Pipelines', 'description': 'Jenkins, GitLab CI, GitHub Actions, automation', 'icon': '🔄', 'keywords': 'cicd, jenkins, github actions, automation, pipeline'},
            {'name': 'Git & Version Control', 'description': 'Git workflows, branching, merging, collaboration', 'icon': '📚', 'keywords': 'git, github, gitlab, version control, branching'},
            {'name': 'Microservices Architecture', 'description': 'Service design, communication, patterns, scalability', 'icon': '🔗', 'keywords': 'microservices, architecture, apis, scalability'},
            {'name': 'System Design', 'description': 'Scalable systems, architecture patterns, trade-offs', 'icon': '🏗️', 'keywords': 'system design, architecture, scalability, patterns'},
            {'name': 'Software Architecture', 'description': 'Design patterns, SOLID, clean architecture, DDD', 'icon': '🏛️', 'keywords': 'architecture, patterns, solid, ddd, clean code'},
            {'name': 'Test-Driven Development', 'description': 'TDD, unit testing, integration tests, test automation', 'icon': '🧪', 'keywords': 'tdd, testing, unittest, pytest, automation'},
            {'name': 'Data Structures & Algorithms', 'description': 'Arrays, trees, graphs, sorting, searching, complexity', 'icon': '📐', 'keywords': 'dsa, algorithms, complexity, leetcode, coding'},
            {'name': 'Computer Science Fundamentals', 'description': 'OS, networks, compilers, theory of computation', 'icon': '💻', 'keywords': 'cs, fundamentals, os, networks, theory'},
            {'name': 'Linux Administration', 'description': 'Shell scripting, system administration, permissions, services', 'icon': '🐧', 'keywords': 'linux, bash, shell, sysadmin, ubuntu'},
            {'name': 'Bash Scripting', 'description': 'Shell scripting, automation, text processing, DevOps', 'icon': '📜', 'keywords': 'bash, shell, scripting, automation, linux'},
            # 51-60
            {'name': 'Terraform', 'description': 'Infrastructure as Code, cloud provisioning, modules', 'icon': '🏗️', 'keywords': 'terraform, iac, cloud, provisioning, hcl'},
            {'name': 'Ansible', 'description': 'Configuration management, playbooks, automation', 'icon': '🔧', 'keywords': 'ansible, automation, configuration, playbooks'},
            {'name': 'Elasticsearch', 'description': 'Search engine, full-text search, analytics, logging', 'icon': '🔍', 'keywords': 'elasticsearch, search, elk, logging, kibana'},
            {'name': 'Apache Kafka', 'description': 'Streaming platform, message queues, real-time data', 'icon': '📨', 'keywords': 'kafka, streaming, messages, realtime, events'},
            {'name': 'RabbitMQ', 'description': 'Message broker, queues, pub/sub, async communication', 'icon': '🐰', 'keywords': 'rabbitmq, messaging, queue, broker, amqp'},
            {'name': 'Natural Language Processing', 'description': 'Text analysis, sentiment, transformers, chatbots', 'icon': '💬', 'keywords': 'nlp, transformers, bert, text, sentiment'},
            {'name': 'Computer Vision', 'description': 'Image processing, object detection, CNNs, OpenCV', 'icon': '👁️', 'keywords': 'cv, opencv, cnn, detection, image'},
            {'name': 'Deep Learning', 'description': 'Neural networks, CNNs, RNNs, transformers, GPUs', 'icon': '🧬', 'keywords': 'deeplearning, neural, cnn, rnn, gpu'},
            {'name': 'TensorFlow', 'description': 'ML framework, model building, training, deployment', 'icon': '🔶', 'keywords': 'tensorflow, ml, keras, models, training'},
            {'name': 'PyTorch', 'description': 'Deep learning framework, dynamic graphs, research', 'icon': '🔥', 'keywords': 'pytorch, deeplearning, neural, research, gpu'},
            # 61-70
            {'name': 'Big Data Engineering', 'description': 'Hadoop, Spark, data pipelines, distributed systems', 'icon': '📊', 'keywords': 'bigdata, hadoop, spark, etl, pipelines'},
            {'name': 'Apache Spark', 'description': 'Distributed computing, data processing, MLlib', 'icon': '⚡', 'keywords': 'spark, distributed, bigdata, processing, scala'},
            {'name': 'Data Engineering', 'description': 'ETL pipelines, data warehousing, Airflow, dbt', 'icon': '🔧', 'keywords': 'dataeng, etl, airflow, warehouse, pipelines'},
            {'name': 'Power BI', 'description': 'Business intelligence, dashboards, data visualization', 'icon': '📈', 'keywords': 'powerbi, bi, dashboards, visualization, microsoft'},
            {'name': 'Tableau', 'description': 'Data visualization, analytics, storytelling, dashboards', 'icon': '📊', 'keywords': 'tableau, visualization, analytics, dashboards'},
            {'name': 'Excel Advanced', 'description': 'Advanced formulas, macros, VBA, data analysis', 'icon': '📗', 'keywords': 'excel, formulas, vba, macros, analysis'},
            {'name': 'R Programming', 'description': 'Statistical computing, data analysis, ggplot2, Shiny', 'icon': '📊', 'keywords': 'r, statistics, ggplot, shiny, analysis'},
            {'name': 'Statistics & Probability', 'description': 'Statistical inference, hypothesis testing, distributions', 'icon': '📐', 'keywords': 'statistics, probability, inference, testing'},
            {'name': 'A/B Testing', 'description': 'Experimentation, hypothesis testing, metrics, analytics', 'icon': '🧪', 'keywords': 'abtesting, experiments, metrics, analytics'},
            {'name': 'Product Analytics', 'description': 'User behavior, metrics, funnels, retention, growth', 'icon': '📱', 'keywords': 'analytics, product, metrics, growth, users'},
            # 71-80
            {'name': 'UI/UX Design', 'description': 'User experience, interface design, prototyping, usability', 'icon': '🎨', 'keywords': 'uiux, design, figma, usability, prototype'},
            {'name': 'Figma Design', 'description': 'Design tool, prototyping, collaboration, components', 'icon': '🎨', 'keywords': 'figma, design, prototype, ui, collaboration'},
            {'name': 'Frontend Performance', 'description': 'Optimization, lazy loading, caching, Core Web Vitals', 'icon': '⚡', 'keywords': 'performance, optimization, webvitals, speed'},
            {'name': 'Web Accessibility', 'description': 'WCAG, ARIA, inclusive design, screen readers', 'icon': '♿', 'keywords': 'a11y, accessibility, wcag, aria, inclusive'},
            {'name': 'Progressive Web Apps', 'description': 'PWA, service workers, offline-first, app-like experience', 'icon': '📱', 'keywords': 'pwa, serviceworker, offline, manifest'},
            {'name': 'WebAssembly', 'description': 'High-performance web code, Rust/C++ to web, gaming', 'icon': '⚙️', 'keywords': 'wasm, webassembly, performance, rust, binary'},
            {'name': 'Three.js & WebGL', 'description': '3D graphics, rendering, animations, game development', 'icon': '🎮', 'keywords': 'threejs, webgl, 3d, graphics, rendering'},
            {'name': 'Game Development', 'description': 'Unity, Unreal, game design, physics, multiplayer', 'icon': '🎮', 'keywords': 'gamedev, unity, unreal, gaming, physics'},
            {'name': 'Unity 3D', 'description': 'Game engine, C# scripting, physics, AR/VR', 'icon': '🎮', 'keywords': 'unity, gamedev, csharp, 3d, arvr'},
            {'name': 'Unreal Engine', 'description': 'AAA game development, Blueprints, C++, graphics', 'icon': '🎮', 'keywords': 'unreal, gamedev, cpp, blueprints, graphics'},
            # 81-90
            {'name': 'Augmented Reality', 'description': 'AR development, ARKit, ARCore, spatial computing', 'icon': '🥽', 'keywords': 'ar, arkit, arcore, spatial, reality'},
            {'name': 'Virtual Reality', 'description': 'VR development, Unity, Oculus, immersive experiences', 'icon': '🥽', 'keywords': 'vr, oculus, unity, immersive, reality'},
            {'name': 'IoT Development', 'description': 'Internet of Things, sensors, Arduino, Raspberry Pi, MQTT', 'icon': '📡', 'keywords': 'iot, sensors, arduino, raspberrypi, mqtt'},
            {'name': 'Embedded Systems', 'description': 'Microcontrollers, real-time systems, firmware, C/C++', 'icon': '🔌', 'keywords': 'embedded, microcontroller, firmware, realtime'},
            {'name': 'Robotics', 'description': 'Robot programming, ROS, sensors, automation, AI', 'icon': '🤖', 'keywords': 'robotics, ros, automation, sensors, ai'},
            {'name': 'Ethical Hacking', 'description': 'Penetration testing, vulnerability assessment, Kali Linux', 'icon': '👨‍💻', 'keywords': 'hacking, pentest, security, kali, vulnerabilities'},
            {'name': 'Network Security', 'description': 'Firewalls, VPNs, intrusion detection, protocols', 'icon': '🛡️', 'keywords': 'network, security, firewall, vpn, ids'},
            {'name': 'Cloud Security', 'description': 'Security in cloud, IAM, encryption, compliance', 'icon': '🔐', 'keywords': 'cloudsecurity, iam, encryption, compliance'},
            {'name': 'Cryptography', 'description': 'Encryption algorithms, PKI, hashing, SSL/TLS', 'icon': '🔒', 'keywords': 'cryptography, encryption, ssl, hashing, pki'},
            {'name': 'GDPR & Compliance', 'description': 'Data privacy, regulations, GDPR, CCPA, compliance', 'icon': '📋', 'keywords': 'gdpr, privacy, compliance, regulations, data'},
            # 91-100
            {'name': 'Quantum Computing', 'description': 'Quantum algorithms, Qiskit, quantum programming', 'icon': '⚛️', 'keywords': 'quantum, qiskit, qubits, algorithms, computing'},
            {'name': 'Edge Computing', 'description': 'Edge devices, distributed computing, low latency', 'icon': '📍', 'keywords': 'edge, distributed, latency, iot, computing'},
            {'name': 'Serverless Architecture', 'description': 'FaaS, Lambda, serverless patterns, event-driven', 'icon': '⚡', 'keywords': 'serverless, lambda, faas, events, cloud'},
            {'name': 'GraphQL API Development', 'description': 'Schema design, resolvers, subscriptions, federation', 'icon': '🔷', 'keywords': 'graphql, api, schema, resolvers, apollo'},
            {'name': 'gRPC', 'description': 'High-performance RPC, Protocol Buffers, streaming', 'icon': '⚡', 'keywords': 'grpc, rpc, protobuf, streaming, api'},
            {'name': 'WebSockets & Real-time', 'description': 'Real-time communication, Socket.io, WebRTC, streaming', 'icon': '🔄', 'keywords': 'websockets, realtime, socketio, webrtc'},
            {'name': 'Content Management Systems', 'description': 'WordPress, Drupal, headless CMS, content delivery', 'icon': '📝', 'keywords': 'cms, wordpress, drupal, contentful, strapi'},
            {'name': 'E-commerce Development', 'description': 'Online stores, Shopify, WooCommerce, payment gateways', 'icon': '🛒', 'keywords': 'ecommerce, shopify, woocommerce, payments'},
            {'name': 'SEO & Digital Marketing', 'description': 'Search optimization, keywords, analytics, content strategy', 'icon': '📈', 'keywords': 'seo, marketing, google, keywords, analytics'},
            {'name': 'Technical Writing', 'description': 'Documentation, API docs, tutorials, technical communication', 'icon': '✍️', 'keywords': 'documentation, writing, technical, docs, guides'}
        ]
        
        print(f"Adding {len(domains_data)} domains...")
        for domain_data in domains_data:
            domain = Domain(
                name=domain_data['name'],
                description=domain_data['description'],
                icon=domain_data['icon'],
                keywords=domain_data['keywords']
            )
            db.session.add(domain)
        
        db.session.commit()
        
        # Verify count
        total = Domain.query.count()
        print(f"✅ Success! Database now has {total} domains")
        
        # Show first 10 and last 10
        print("\nFirst 10 domains:")
        for domain in Domain.query.limit(10).all():
            print(f"  - {domain.icon} {domain.name}")
        
        print("\nLast 10 domains:")
        for domain in Domain.query.order_by(Domain.id.desc()).limit(10).all():
            print(f"  - {domain.icon} {domain.name}")

if __name__ == '__main__':
    reset_domains()

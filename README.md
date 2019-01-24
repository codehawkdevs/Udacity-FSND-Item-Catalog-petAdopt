# Item Catalog(PetAdopt)
This web app is a project for the Udacity [FSND Course](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).

### Project Overview
> To Develop an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

### Why This Project?
> Modern web applications perform a variety of functions and provide amazing features and utilities to their users; but deep down, it’s really all just creating, reading, updating and deleting data. In this project, I combined my knowledge of building dynamic websites with persistent data storage to create a web application that provides a compelling service to your users.

### What Did I Learn?
  * Develop a RESTful web application using the Python framework Flask
  * Implementing third-party OAuth authentication.
  * Implementing CRUD (create, read, update and delete) operations.
  
### How to Run?

#### PreRequisites
  * [Python ~3.7](https://www.python.org/)
  * [Vagrant](https://www.vagrantup.com/)
  * [VirtualBox](https://www.virtualbox.org/)
  
#### Setup Project:
  1. Install Vagrant and VirtualBox
  2. Download or Clone [fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm) repository.
  3. Find the catalog folder and replace it with the content of this current repository.

#### Launch Project
  1. Launch the Vagrant VM using command:
  
  ```
    $ vagrant up
  ```
  2. Create the database with following command

  ```
    $ python /vagrant/item-catalog/database_setup.py
  ```

  3. Insert fake data into database for testing purposes

  ```
  $ python /vagrant/item-catalog/insertdata.py
  ```

  4. Run your application within the VM
  
  ```
    $ python /vagrant/item-catalog/project.py
  ```
  5. Access and test your application by visiting [http://localhost:8000](http://localhost:8000).

#### JSON Endpoints
The following are open to the public:

Categories JSON: `/pets/JSON`
    - Displays all categories

Category Items JSON: `/pets/<path:category_id>/items/JSON`
    - Displays items (pets) for a specific category

Category Item JSON: `/pets/<path:category_id>/<path:pet_id>/JSON`
    - Displays a specific category item(pet).

#### If you're running into issues:
contact me on [twitter](https://www.twitter.com/harshsahu97/)
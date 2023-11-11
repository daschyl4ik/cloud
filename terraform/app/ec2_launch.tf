#creating security group
resource "aws_security_group" "main" {
  name        = "flask_app_sg"
  description = "web and ssh"

  ingress {
    description      = "https"
    from_port        = 0
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "http"
    from_port        = 0
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

ingress {
    description      = "ssh"
    from_port        = 22
    to_port          = 22
    protocol         = "TCP"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  
#Security groups are stateful—if you send a request from your instance, 
#the response traffic for that request is allowed to flow in regardless of inbound security group rules.

#any outgoing traffic is allowed
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "flask_app_sg"
  }
}


#launch instance
resource "aws_instance" "main" {
  ami           = "ami-0c9b2924fcd9b73a4"     #free tier eligible, Ubuntu, 22.04 LTS, amd64
  instance_type = "t3.micro"                  #free tier eligible

  credit_specification {
    cpu_credits = "standard"
  }

root_block_device {
  volume_type = "gp3"
  volume_size = 8
  iops = 3000
}

tags = {
  Name = "flask_app_ec2"
}

user_data = templatefile("userdata.sh.tftpl", {
  user = "app_admin",
  public_key = var.public_key
})

vpc_security_group_ids = [aws_security_group.main.id]

}
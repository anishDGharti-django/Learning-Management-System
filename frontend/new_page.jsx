{currentItems?.map((c, index) => (
    <div className="col">
      {/* Card */}
      <div className="card card-hover">
        <Link to={`/course-detail/${c.slug}/`}>
          <img
            src={c.image}
            alt="course"
            className="card-img-top"
            style={{
              width: "100%",
              height: "200px",
              objectFit: "cover",
            }}
          />
        </Link>
        {/* Card Body */}
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <div>
              <span className="badge bg-info">{c.level}</span>
              <span className="badge bg-success ms-2">
                {c.language}
              </span>
            </div>
            <a onClick={() => addToWishlist(c.id)} className="fs-5">
              <i className="fas fa-heart text-danger align-middle" />
            </a>
          </div>
          <h4 className="mb-2 text-truncate-line-2 ">
            <Link
              to={`/course-detail/slug/`}
              className="text-inherit text-decoration-none text-dark fs-5"
            >
              {c.title}
            </Link>
          </h4>
          <small>By: {c.teacher.full_name}</small> <br />
          <small>
            {c.students?.length} Student
            {c.students?.length > 1 && "s"}
          </small>{" "}
          <br />
          <div className="lh-1 mt-3 d-flex">
            <span className="align-text-top">
              <span className="fs-6">
                <Rater total={5} rating={c.average_rating || 0} />
              </span>
            </span>
            <span className="text-warning">4.5</span>
            <span className="fs-6 ms-2">
              ({c.reviews?.length} Reviews)
            </span>
          </div>
        </div>
        {/* Card Footer */}
        <div className="card-footer">
          <div className="row align-items-center g-0">
            <div className="col">
              <h5 className="mb-0">${c.price}</h5>
            </div>
            <div className="col-auto">
              <button
                type="button"
                onClick={() =>
                  addToCart(
                    c.id,
                    userId,
                    c.price,
                    country,
                    cartId
                  )
                }
                className="text-inherit text-decoration-none btn btn-primary me-2"
              >
                <i className="fas fa-shopping-cart text-primary text-white" />
              </button>
              <Link
                to={""}
                className="text-inherit text-decoration-none btn btn-primary"
              >
                Enroll Now{" "}
                <i className="fas fa-arrow-right text-primary align-middle me-2 text-white" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  ))}